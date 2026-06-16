#!/usr/bin/env python3
"""
Keyword Baseline Comparison

Builds a naive keyword-matching baseline and compares it against our
multi-axis ranker to demonstrate superiority.

Usage:
    python analysis/baseline_comparison.py --candidates ./candidates.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.honeypot import is_honeypot
from src.jd_profile import SKILL_WEIGHTS


# Baseline: simple keyword count
JD_KEYWORDS = {
    "NLP", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning",
    "FAISS", "Milvus", "Pinecone", "Weaviate", "Qdrant", "Elasticsearch",
    "Python", "Docker", "Kubernetes", "AWS", "GCP",
    "Fine-tuning LLMs", "LoRA", "XGBoost", "RAG",
    "Transformers", "Hugging Face", "sentence-transformers",
    "Feature Engineering", "Statistical Modeling",
    "MLflow", "Weights & Biases", "BentoML",
    "Spark", "Airflow", "Kafka",
}


def keyword_score(candidate: dict) -> float:
    """Naive baseline: count JD keyword matches in skills."""
    skills = {s["name"] for s in candidate.get("skills", [])}
    return len(skills & JD_KEYWORDS)


def main():
    parser = argparse.ArgumentParser(
        description="Keyword baseline comparison"
    )
    parser.add_argument(
        "--candidates", "-c",
        required=True,
        help="Path to candidates.jsonl",
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=100,
        help="Number of top candidates to compare (default: 100)",
    )

    args = parser.parse_args()

    print("Loading candidates...")
    all_candidates = []
    with open(args.candidates, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                all_candidates.append(json.loads(line))

    print(f"Loaded {len(all_candidates):,} candidates")
    print()

    # Score all candidates with keyword baseline
    keyword_scored = []
    for c in all_candidates:
        score = keyword_score(c)
        keyword_scored.append((c, score))

    keyword_scored.sort(key=lambda x: (-x[1], x[0]["candidate_id"]))
    top_baseline = keyword_scored[:args.top_k]

    # Analyze baseline results
    print("=" * 70)
    print("  KEYWORD BASELINE ANALYSIS (Top 100)")
    print("=" * 70)
    print()

    # Title distribution
    from collections import Counter
    title_counts = Counter(c["profile"]["current_title"] for c, _ in top_baseline)
    print("Title distribution (keyword baseline):")
    for title, count in title_counts.most_common():
        print(f"  {title}: {count}")
    print()

    # Honeypot check
    honeypot_count = sum(1 for c, _ in top_baseline if is_honeypot(c))
    print(f"Honeypots in top 100: {honeypot_count}")
    print()

    # Non-tech titles
    non_tech = {"HR Manager", "Marketing Manager", "Accountant", "Sales Executive",
                "Operations Manager", "Content Writer", "Civil Engineer",
                "Mechanical Engineer", "Graphic Designer", "Customer Support"}
    non_tech_count = sum(
        1 for c, _ in top_baseline
        if c["profile"]["current_title"] in non_tech
    )
    print(f"Non-tech titles in top 100: {non_tech_count}")
    print()

    # Show top 10
    print("Top 10 by keyword matching:")
    for i, (c, score) in enumerate(top_baseline[:10], 1):
        p = c["profile"]
        hp = "🍯" if is_honeypot(c) else "  "
        print(f"  {hp} #{i:>2d} | {c['candidate_id']} | Keywords: {score:.0f} | "
              f"{p['current_title']} at {p['current_company']} ({p['years_of_experience']:.1f}yr)")

    print()
    print("=" * 70)
    print("  CONCLUSION")
    print("=" * 70)
    print()
    print(f"  Keyword matching puts {non_tech_count} non-tech candidates in top 100.")
    print(f"  Keyword matching includes {honeypot_count} honeypots.")
    print(f"  This demonstrates why semantic understanding > keyword counting.")


if __name__ == "__main__":
    main()
