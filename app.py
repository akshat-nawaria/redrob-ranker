"""
Streamlit Sandbox Application for Redrob Candidate Ranker

A minimal demo app that lets you upload a small candidate sample and
see the ranking results interactively.

Run:
    streamlit run app.py
"""

import streamlit as st
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.filters import passes_hard_filters
from src.scorer import compute_all_scores, compute_base_score
from src.behavior import compute_behavioral_modifier
from src.explain import generate_reasoning
from src.honeypot import detect_honeypot_signals, get_honeypot_report


# ---- Page Config ----
st.set_page_config(
    page_title="Redrob Candidate Ranker",
    page_icon="🎯",
    layout="wide",
)

# ---- Header ----
st.title("🎯 Redrob Intelligent Candidate Ranker")
st.markdown("""
**Beyond Keywords** — An AI ranking system that understands who actually fits
the role, not just who has the right buzzwords.

*Upload candidates in JSON/JSONL format to see them ranked for the
Senior AI Engineer role.*
""")

st.divider()


def process_candidates(candidates: list[dict]) -> list[dict]:
    """Run the ranking pipeline on a list of candidates."""
    scored = []
    filtered_out = []

    for candidate in candidates:
        passes, reason = passes_hard_filters(candidate)
        if not passes:
            filtered_out.append({
                "candidate_id": candidate["candidate_id"],
                "name": candidate["profile"]["anonymized_name"],
                "title": candidate["profile"]["current_title"],
                "reason": reason,
                "honeypot_signals": detect_honeypot_signals(candidate),
            })
            continue

        scores = compute_all_scores(candidate)
        base_score = compute_base_score(scores)
        modifier = compute_behavioral_modifier(candidate)
        final_score = base_score * modifier

        scored.append({
            "candidate": candidate,
            "scores": scores,
            "base_score": base_score,
            "modifier": modifier,
            "final_score": final_score,
        })

    # Sort
    scored.sort(key=lambda x: (-x["final_score"], x["candidate"]["candidate_id"]))

    # Generate reasoning
    results = []
    for rank, entry in enumerate(scored, 1):
        reasoning = generate_reasoning(
            candidate=entry["candidate"],
            scores=entry["scores"],
            final_score=entry["final_score"],
            rank=rank,
        )
        results.append({
            "rank": rank,
            "candidate_id": entry["candidate"]["candidate_id"],
            "name": entry["candidate"]["profile"]["anonymized_name"],
            "title": entry["candidate"]["profile"]["current_title"],
            "company": entry["candidate"]["profile"]["current_company"],
            "yoe": entry["candidate"]["profile"]["years_of_experience"],
            "industry": entry["candidate"]["profile"]["current_industry"],
            "location": f"{entry['candidate']['profile']['location']}, {entry['candidate']['profile']['country']}",
            "base_score": round(entry["base_score"], 4),
            "modifier": round(entry["modifier"], 4),
            "final_score": round(entry["final_score"], 4),
            "reasoning": reasoning,
            "scores": entry["scores"],
        })

    return results, filtered_out


# ---- File Upload ----
col1, col2 = st.columns([2, 1])

with col1:
    uploaded = st.file_uploader(
        "Upload candidates (JSON array or JSONL)",
        type=["json", "jsonl"],
    )

with col2:
    st.info(
        "**Accepted formats:**\n"
        "- `.json` — JSON array of candidates\n"
        "- `.jsonl` — One candidate per line"
    )

# ---- Demo with sample data ----
use_sample = st.checkbox("Or use sample data (first 20 candidates from sample_candidates.json)")

candidates = None

if uploaded is not None:
    content = uploaded.read().decode("utf-8")
    try:
        # Try JSON array first
        candidates = json.loads(content)
        if isinstance(candidates, dict):
            candidates = [candidates]
    except json.JSONDecodeError:
        # Try JSONL
        candidates = []
        for line in content.strip().split("\n"):
            if line.strip():
                candidates.append(json.loads(line))

elif use_sample:
    # Try to load sample data
    sample_paths = [
        Path(__file__).parent / "sample_candidates.json",
        Path(r"c:\Users\Akshyat\Downloads\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\sample_candidates.json"),
    ]
    for sp in sample_paths:
        if sp.exists():
            with open(sp, "r", encoding="utf-8") as f:
                candidates = json.loads(f.read())[:20]
            break

if candidates:
    st.success(f"Loaded **{len(candidates)}** candidates")

    # Run pipeline
    with st.spinner("🔍 Ranking candidates..."):
        results, filtered_out = process_candidates(candidates)

    # ---- Results ----
    st.header(f"📊 Results: {len(results)} ranked, {len(filtered_out)} filtered")

    # Tab layout
    tab1, tab2, tab3 = st.tabs(["🏆 Rankings", "🚫 Filtered Out", "🔬 Deep Dive"])

    with tab1:
        if results:
            for r in results:
                with st.expander(
                    f"**#{r['rank']}** — {r['name']} | {r['title']} at {r['company']} "
                    f"| Score: {r['final_score']:.4f}"
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Base Score", f"{r['base_score']:.4f}")
                    c2.metric("Behavioral Modifier", f"{r['modifier']:.4f}")
                    c3.metric("Final Score", f"{r['final_score']:.4f}")

                    st.markdown(f"**Experience:** {r['yoe']} years")
                    st.markdown(f"**Industry:** {r['industry']}")
                    st.markdown(f"**Location:** {r['location']}")

                    st.markdown("**Reasoning:**")
                    st.info(r["reasoning"])

                    st.markdown("**Score Breakdown:**")
                    score_cols = st.columns(4)
                    axes = list(r["scores"].items())
                    for i, (axis, score) in enumerate(axes):
                        score_cols[i % 4].metric(
                            axis.replace("_", " ").title(),
                            f"{score:.3f}",
                        )
        else:
            st.warning("No candidates passed the filters.")

    with tab2:
        if filtered_out:
            for f_out in filtered_out:
                icon = "🍯" if "honeypot" in f_out["reason"] else "❌"
                st.markdown(
                    f"{icon} **{f_out['candidate_id']}** — "
                    f"{f_out['name']} ({f_out['title']}) → "
                    f"*{f_out['reason']}*"
                )
                if f_out.get("honeypot_signals"):
                    st.caption(f"  Honeypot signals: {f_out['honeypot_signals']}")
        else:
            st.info("No candidates were filtered out.")

    with tab3:
        if results:
            st.subheader("Score Distribution")

            import collections
            # Simple text-based score breakdown
            for r in results[:10]:
                st.markdown(f"**#{r['rank']} {r['name']}** (Score: {r['final_score']:.4f})")
                axes = r["scores"]
                bar = ""
                for axis, score in axes.items():
                    width = int(score * 20)
                    bar += f"  {axis:20s}: {'█' * width}{'░' * (20 - width)} {score:.3f}\n"
                st.code(bar)

else:
    st.markdown("👆 Upload a candidate file or check the sample data box to get started.")

# ---- Footer ----
st.divider()
st.caption(
    "Built for the Redrob Intelligent Candidate Discovery & Ranking Challenge. "
    "This system uses multi-axis scoring with trust-weighted skill verification "
    "and behavioral signal modifiers. No LLMs or external APIs are used during ranking."
)
