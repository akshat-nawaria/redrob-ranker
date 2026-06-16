#!/usr/bin/env python3
"""
Score Distribution Analysis

Analyzes the output submission to verify score distribution, candidate
diversity, and quality metrics.

Usage:
    python analysis/score_analysis.py --submission ./submission.csv --candidates ./candidates.jsonl
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.honeypot import detect_honeypot_signals
from src.jd_profile import TITLE_RELEVANCE, INDUSTRY_RELEVANCE


def load_submission(path: str) -> list[dict]:
    """Load and parse submission CSV."""
    results = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "candidate_id": row["candidate_id"],
                "rank": int(row["rank"]),
                "score": float(row["score"]),
                "reasoning": row.get("reasoning", ""),
            })
    return sorted(results, key=lambda x: x["rank"])


def load_candidates_index(path: str) -> dict:
    """Load candidates into a dict keyed by candidate_id."""
    index = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                index[c["candidate_id"]] = c
    return index


def analyze(submission_path: str, candidates_path: str):
    """Run all analysis checks."""
    print("=" * 70)
    print("  Submission Analysis Report")
    print("=" * 70)
    print()

    # Load data
    submission = load_submission(submission_path)
    print(f"Loading candidate index from {candidates_path}...")
    candidates = load_candidates_index(candidates_path)
    print(f"Loaded {len(candidates):,} candidates")
    print()

    # ---- Basic checks ----
    print("1. BASIC VALIDATION")
    print("-" * 40)
    print(f"  Rows: {len(submission)} (expected: 100)")
    ranks = [r["rank"] for r in submission]
    print(f"  Rank range: {min(ranks)}-{max(ranks)}")
    print(f"  Unique ranks: {len(set(ranks))}")
    scores = [r["score"] for r in submission]
    is_monotonic = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    print(f"  Scores monotonic: {'YES [OK]' if is_monotonic else 'NO [FAIL]'}")
    ids = [r["candidate_id"] for r in submission]
    print(f"  Unique IDs: {len(set(ids))}")
    all_exist = all(cid in candidates for cid in ids)
    print(f"  All IDs exist: {'YES [OK]' if all_exist else 'NO [FAIL]'}")
    print()

    # ---- Score distribution ----
    print("2. SCORE DISTRIBUTION")
    print("-" * 40)
    print(f"  Max:    {max(scores):.4f}")
    print(f"  Min:    {min(scores):.4f}")
    print(f"  Mean:   {sum(scores)/len(scores):.4f}")
    print(f"  Median: {sorted(scores)[50]:.4f}")
    print(f"  Spread: {max(scores) - min(scores):.4f}")
    print()

    # ---- Title distribution ----
    print("3. TITLE DISTRIBUTION IN TOP 100")
    print("-" * 40)
    title_counts = Counter()
    for r in submission:
        cid = r["candidate_id"]
        if cid in candidates:
            title = candidates[cid]["profile"]["current_title"]
            title_counts[title] += 1
    for title, count in title_counts.most_common():
        score = TITLE_RELEVANCE.get(title, 0)
        flag = " [!]" if score < 0.2 else ""
        print(f"  {title}: {count}{flag}")
    print()

    # ---- Industry distribution ----
    print("4. INDUSTRY DISTRIBUTION IN TOP 100")
    print("-" * 40)
    industry_counts = Counter()
    for r in submission:
        cid = r["candidate_id"]
        if cid in candidates:
            industry = candidates[cid]["profile"]["current_industry"]
            industry_counts[industry] += 1
    for industry, count in industry_counts.most_common():
        print(f"  {industry}: {count}")
    print()

    # ---- Country distribution ----
    print("5. COUNTRY DISTRIBUTION IN TOP 100")
    print("-" * 40)
    country_counts = Counter()
    for r in submission:
        cid = r["candidate_id"]
        if cid in candidates:
            country = candidates[cid]["profile"]["country"]
            country_counts[country] += 1
    for country, count in country_counts.most_common():
        print(f"  {country}: {count}")
    print()

    # ---- Experience distribution ----
    print("6. EXPERIENCE DISTRIBUTION IN TOP 100")
    print("-" * 40)
    exp_vals = []
    for r in submission:
        cid = r["candidate_id"]
        if cid in candidates:
            yoe = candidates[cid]["profile"]["years_of_experience"]
            exp_vals.append(yoe)
    if exp_vals:
        print(f"  Range: {min(exp_vals):.1f} - {max(exp_vals):.1f} years")
        print(f"  Mean:  {sum(exp_vals)/len(exp_vals):.1f} years")
        in_band = sum(1 for y in exp_vals if 5 <= y <= 9)
        print(f"  In 5-9yr band: {in_band}/100")
    print()

    # ---- Honeypot check ----
    print("7. HONEYPOT CHECK")
    print("-" * 40)
    honeypot_count = 0
    for r in submission:
        cid = r["candidate_id"]
        if cid in candidates:
            signals = detect_honeypot_signals(candidates[cid])
            if len(signals) >= 2:
                honeypot_count += 1
                print(f"  [!] {cid} (rank {r['rank']}): {signals}")
    print(f"  Total honeypots in top 100: {honeypot_count} "
          f"({'PASS [OK]' if honeypot_count <= 10 else 'FAIL [>10%]'})")
    print()

    # ---- Reasoning quality ----
    print("8. REASONING QUALITY")
    print("-" * 40)
    empty = sum(1 for r in submission if not r["reasoning"].strip())
    print(f"  Empty reasoning: {empty}")
    reasoning_set = set(r["reasoning"] for r in submission)
    print(f"  Unique reasoning strings: {len(reasoning_set)}/100")
    avg_len = sum(len(r["reasoning"]) for r in submission) / len(submission)
    print(f"  Average reasoning length: {avg_len:.0f} chars")
    print()

    # ---- Top 10 detailed view ----
    print("9. TOP 10 CANDIDATES")
    print("-" * 40)
    for r in submission[:10]:
        cid = r["candidate_id"]
        if cid in candidates:
            c = candidates[cid]
            p = c["profile"]
            print(f"  #{r['rank']:>2d} | {cid} | Score: {r['score']:.4f}")
            print(f"       {p['current_title']} at {p['current_company']} "
                  f"({p['years_of_experience']:.1f}yr)")
            print(f"       {p['current_industry']} | "
                  f"{p['location']}, {p['country']}")
            print(f"       Reasoning: {r['reasoning'][:120]}...")
            print()

    print("=" * 70)
    print("  Analysis complete")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze submission quality and distribution"
    )
    parser.add_argument(
        "--submission", "-s",
        default="./submission.csv",
        help="Path to submission CSV",
    )
    parser.add_argument(
        "--candidates", "-c",
        required=True,
        help="Path to candidates.jsonl",
    )

    args = parser.parse_args()
    analyze(args.submission, args.candidates)


if __name__ == "__main__":
    main()
