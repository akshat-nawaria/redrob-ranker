#!/usr/bin/env python3
"""
Redrob Intelligent Candidate Ranking System
============================================

Main entry point for the ranking pipeline.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Architecture:
    Stage 1: Hard Filters     → Eliminate honeypots, non-tech, consulting-only
    Stage 2: Multi-Axis Scoring → 8-axis weighted score with trust-weighting
    Stage 3: Behavioral Modifier → Multiplicative engagement signal
    Stage 4: Rank + Explain   → Top 100 with data-grounded reasoning

Runtime: <60 seconds on CPU | Memory: <4GB | No GPU | No network
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.filters import passes_hard_filters
from src.scorer import compute_all_scores, compute_base_score
from src.behavior import compute_behavioral_modifier
from src.explain import generate_reasoning
from src.honeypot import detect_honeypot_signals
from src.utils import (
    stream_candidates,
    write_submission_csv,
    Timer,
    print_candidate_summary,
)


# Number of candidates to output in the submission
TOP_K = 100


def run_pipeline(candidates_path: str, output_path: str, verbose: bool = True):
    """
    Execute the full ranking pipeline end-to-end.

    Args:
        candidates_path: Path to candidates.jsonl
        output_path: Path to write submission.csv
        verbose: Print progress and debug info
    """
    pipeline_start = time.perf_counter()

    if verbose:
        print("=" * 70)
        print("  Redrob Intelligent Candidate Ranking System v1.0")
        print("=" * 70)
        print()

    # -----------------------------------------------------------------
    # Stage 1 + 2 + 3: Stream through candidates, filter, score, modify
    # -----------------------------------------------------------------
    scored_candidates = []
    total_count = 0
    filtered_count = 0
    honeypot_count = 0
    filter_reasons = {}

    with Timer("Full Pipeline"):
        if verbose:
            print("Processing candidates...")
            print()

        for candidate in stream_candidates(candidates_path):
            total_count += 1

            # Progress indicator
            if verbose and total_count % 10000 == 0:
                print(f"  Processed {total_count:,} candidates...")

            # Stage 1: Hard filters
            passes, reason = passes_hard_filters(candidate)
            if not passes:
                filtered_count += 1
                filter_reasons[reason.split("(")[0]] = (
                    filter_reasons.get(reason.split("(")[0], 0) + 1
                )
                if "honeypot" in reason:
                    honeypot_count += 1
                continue

            # Stage 2: Multi-axis scoring
            scores = compute_all_scores(candidate)
            base_score = compute_base_score(scores)

            # Stage 3: Behavioral modifier
            modifier = compute_behavioral_modifier(candidate)
            final_score = base_score * modifier

            scored_candidates.append({
                "candidate": candidate,
                "scores": scores,
                "base_score": base_score,
                "modifier": modifier,
                "final_score": final_score,
            })

    if verbose:
        print()
        print(f"  Total candidates processed: {total_count:,}")
        print(f"  Filtered out:              {filtered_count:,}")
        print(f"    - Honeypots detected:    {honeypot_count}")
        print(f"  Candidates scored:         {len(scored_candidates):,}")
        print()
        print("  Filter breakdown:")
        for reason, count in sorted(
            filter_reasons.items(), key=lambda x: -x[1]
        ):
            print(f"    {reason}: {count:,}")
        print()

    # -----------------------------------------------------------------
    # Stage 4: Sort, select top 100, generate reasoning
    # -----------------------------------------------------------------
    with Timer("Ranking + Explanation"):
        # Sort by final score descending, then candidate_id ascending for ties.
        # IMPORTANT: round to 4 decimals BEFORE sorting so that tie-breaking
        # matches the precision written to the CSV (validator checks this).
        for entry in scored_candidates:
            entry["final_score_rounded"] = round(entry["final_score"], 4)

        scored_candidates.sort(
            key=lambda x: (-x["final_score_rounded"], x["candidate"]["candidate_id"])
        )

        # Take top 100
        top_k = scored_candidates[:TOP_K]

        # Generate reasoning for each
        results = []
        for rank_idx, entry in enumerate(top_k, 1):
            reasoning = generate_reasoning(
                candidate=entry["candidate"],
                scores=entry["scores"],
                final_score=entry["final_score"],
                rank=rank_idx,
            )

            results.append({
                "candidate_id": entry["candidate"]["candidate_id"],
                "rank": rank_idx,
                "score": entry["final_score_rounded"],
                "reasoning": reasoning,
            })

    # -----------------------------------------------------------------
    # Write output
    # -----------------------------------------------------------------
    with Timer("Write CSV"):
        write_submission_csv(results, output_path)

    pipeline_elapsed = time.perf_counter() - pipeline_start

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------
    if verbose:
        print()
        print("=" * 70)
        print(f"  PIPELINE COMPLETE in {pipeline_elapsed:.2f}s")
        print(f"  Output: {output_path}")
        print("=" * 70)
        print()

        # Show top 10
        print("  TOP 10 CANDIDATES:")
        print("  " + "-" * 66)
        for entry in top_k[:10]:
            print_candidate_summary(
                entry["candidate"],
                results[top_k.index(entry)]["rank"],
                entry["final_score"],
            )

        # Show score distribution
        scores_list = [e["final_score"] for e in top_k]
        print(f"  Score range: {min(scores_list):.4f} - {max(scores_list):.4f}")
        print(f"  Score mean:  {sum(scores_list)/len(scores_list):.4f}")
        print(f"  Score median: {sorted(scores_list)[len(scores_list)//2]:.4f}")
        print()

        # Honeypot check on top 100
        honeypots_in_top = sum(
            1 for e in top_k
            if len(detect_honeypot_signals(e["candidate"])) >= 2
        )
        print(f"  Honeypots in top 100: {honeypots_in_top} "
              f"({'PASS [OK]' if honeypots_in_top <= 10 else 'FAIL [>10%!!]'})")
        print()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Redrob Intelligent Candidate Ranking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
    python rank.py -c data/candidates.jsonl -o results/my_submission.csv --quiet
        """,
    )
    parser.add_argument(
        "--candidates", "-c",
        required=True,
        help="Path to candidates.jsonl file",
    )
    parser.add_argument(
        "--out", "-o",
        default="./submission.csv",
        help="Path for output submission CSV (default: ./submission.csv)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output",
    )

    args = parser.parse_args()

    # Validate input file
    if not Path(args.candidates).exists():
        print(f"ERROR: Candidates file not found: {args.candidates}")
        sys.exit(1)

    run_pipeline(
        candidates_path=args.candidates,
        output_path=args.out,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
