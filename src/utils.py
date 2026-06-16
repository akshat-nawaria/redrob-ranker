"""
Utility Functions

Shared helpers used across the pipeline.
"""

import json
import csv
import time
import sys
from pathlib import Path


def stream_candidates(filepath: str):
    """
    Memory-efficient generator that yields one candidate at a time
    from a JSONL file.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Candidate file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(
                    f"WARNING: Skipping malformed JSON at line {line_num}: {e}",
                    file=sys.stderr,
                )


def write_submission_csv(
    ranked_results: list[dict],
    output_path: str,
) -> None:
    """
    Write the final submission CSV.

    Args:
        ranked_results: List of dicts with keys:
            candidate_id, rank, score, reasoning
        output_path: Path to write the CSV.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for row in ranked_results:
            writer.writerow([
                row["candidate_id"],
                row["rank"],
                f"{row['score']:.4f}",
                row["reasoning"],
            ])


class Timer:
    """Simple context manager for timing pipeline stages."""

    def __init__(self, name: str):
        self.name = name
        self.start = None
        self.elapsed = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        print(f"  [{self.name}] {self.elapsed:.2f}s")


def format_score(score: float, decimals: int = 4) -> str:
    """Format a score for display."""
    return f"{score:.{decimals}f}"


def print_candidate_summary(candidate: dict, rank: int, score: float) -> None:
    """Pretty-print a candidate summary for debugging."""
    p = candidate["profile"]
    s = candidate["redrob_signals"]
    skills = candidate.get("skills", [])

    print(f"  Rank {rank:>3d} | {candidate['candidate_id']} | "
          f"Score: {score:.4f}")
    print(f"         | {p['current_title']} at {p['current_company']} "
          f"({p['years_of_experience']:.1f}yr)")
    print(f"         | Industry: {p['current_industry']} | "
          f"Location: {p['location']}, {p['country']}")
    print(f"         | Skills: {len(skills)} total | "
          f"Response Rate: {s['recruiter_response_rate']:.0%} | "
          f"Notice: {s['notice_period_days']}d")
    print()
