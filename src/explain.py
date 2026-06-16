"""
Explanation Generation Module

Stage 4 of the pipeline: generate specific, data-grounded reasoning for each
ranked candidate. Every claim in the reasoning must be verifiable from the
candidate's actual profile data.

Quality constraints from submission_spec:
  - NO empty reasoning
  - NO identical/templated strings
  - NO hallucinated skills or companies
  - Reasoning must connect to JD requirements
  - Rank-consistent tone (top-10 = enthusiastic, bottom-50 = measured)
  - Honest concerns for weaker candidates
"""

from src.jd_profile import SKILL_WEIGHTS, PREFERRED_CITIES, PREFERRED_COUNTRY


def generate_reasoning(
    candidate: dict,
    scores: dict,
    final_score: float,
    rank: int,
) -> str:
    """
    Generate a 1-2 sentence reasoning grounded in the candidate's actual data.

    Args:
        candidate: Full candidate dict.
        scores: Dict of axis_name → score from the scorer.
        final_score: The final composite score.
        rank: 1-based rank position.

    Returns:
        A reasoning string.
    """
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    parts = []

    # -----------------------------------------------------------------
    # Part 1: Role identity (always included)
    # -----------------------------------------------------------------
    parts.append(
        f"{profile['current_title']} at {profile['current_company']} "
        f"({profile['years_of_experience']:.1f}yr exp, "
        f"{profile['current_industry']})"
    )

    # -----------------------------------------------------------------
    # Part 2: Top relevant skills with trust evidence
    # -----------------------------------------------------------------
    relevant_skills = []
    for s in skills:
        weight = SKILL_WEIGHTS.get(s["name"], 0)
        if weight >= 1.5:
            relevant_skills.append((s, weight))

    relevant_skills.sort(key=lambda x: x[1], reverse=True)
    top_skills = relevant_skills[:4]

    if top_skills:
        skill_strs = []
        for s, w in top_skills:
            dur = s.get("duration_months", 0)
            prof = s.get("proficiency", "beginner")
            skill_strs.append(f"{s['name']} ({dur}mo, {prof})")
        parts.append("skills: " + ", ".join(skill_strs))

    # -----------------------------------------------------------------
    # Part 3: Career highlight (what did they actually build?)
    # -----------------------------------------------------------------
    career_highlight = _extract_career_highlight(career)
    if career_highlight:
        parts.append(career_highlight)

    # -----------------------------------------------------------------
    # Part 4: Industry/domain fit
    # -----------------------------------------------------------------
    if scores.get("domain_industry", 0) >= 0.6:
        parts.append(f"strong domain fit ({profile['current_industry']})")

    # -----------------------------------------------------------------
    # Part 5: Location
    # -----------------------------------------------------------------
    if profile.get("country") == PREFERRED_COUNTRY:
        location = profile.get("location", "India")
        loc_lower = location.lower()
        if any(c in loc_lower for c in ["pune", "noida"]):
            parts.append(f"based in {location} (ideal location)")
        else:
            parts.append(f"based in {location}, India")
    else:
        parts.append(
            f"based in {profile.get('location', 'unknown')}, "
            f"{profile.get('country', 'unknown')}"
        )

    # -----------------------------------------------------------------
    # Part 6: Behavioral highlights (select 1-2 most relevant)
    # -----------------------------------------------------------------
    behavioral = _get_behavioral_highlights(signals)
    if behavioral:
        parts.append(behavioral)

    # -----------------------------------------------------------------
    # Part 7: Honest concerns (for candidates ranked >30)
    # -----------------------------------------------------------------
    if rank > 30:
        concerns = _get_concerns(candidate, scores)
        if concerns:
            parts.append(f"gap: {concerns}")

    # Assemble: use semicolons to separate, keep under 2 sentences
    reasoning = "; ".join(parts) + "."

    # Safety: truncate if too long (keep it readable for judges)
    if len(reasoning) > 500:
        reasoning = reasoning[:497] + "..."

    return reasoning


def _extract_career_highlight(career: list[dict]) -> str:
    """
    Extract the most relevant career description highlight.
    """
    if not career:
        return ""

    # Focus on the current/most recent role
    desc = career[0].get("description", "").lower()

    # Priority 1: ranking/retrieval/search systems
    if any(kw in desc for kw in [
        "ranking", "retrieval", "search system", "search quality",
        "recommendation system", "recommender",
    ]):
        return "career shows production ranking/retrieval/search system work"

    # Priority 2: ML model deployment
    if any(kw in desc for kw in [
        "deployed model", "model deployment", "production ml",
        "model serving", "inference pipeline", "ml pipeline",
    ]):
        return "career includes production ML model deployment"

    # Priority 3: embeddings/NLP
    if any(kw in desc for kw in [
        "embedding", "nlp", "natural language", "text classification",
        "transformer", "bert", "fine-tun",
    ]):
        return "career includes NLP/embeddings work"

    # Priority 4: data/ML engineering
    if any(kw in desc for kw in [
        "data pipeline", "ml", "machine learning", "deep learning",
        "neural", "model training", "feature engineering",
    ]):
        return "career includes ML/data engineering work"

    # Priority 5: general engineering
    if any(kw in desc for kw in [
        "backend", "api", "microservice", "distributed",
        "python", "spark", "kafka",
    ]):
        return "solid backend/data engineering foundation"

    return ""


def _get_behavioral_highlights(signals: dict) -> str:
    """
    Select 1-2 most notable behavioral signals.
    """
    highlights = []

    # Response rate
    rr = signals.get("recruiter_response_rate", 0)
    if rr >= 0.6:
        highlights.append(f"highly responsive ({rr:.0%} rate)")
    elif rr >= 0.4:
        highlights.append(f"responsive ({rr:.0%} rate)")

    # Open to work
    if signals.get("open_to_work_flag"):
        highlights.append("actively looking")

    # Notice period
    notice = signals.get("notice_period_days", 60)
    if notice <= 30:
        highlights.append(f"{notice}-day notice")

    # GitHub
    github = signals.get("github_activity_score", -1)
    if github >= 50:
        highlights.append(f"active on GitHub (score {github:.0f}/100)")

    # Pick top 2
    return ", ".join(highlights[:2]) if highlights else ""


def _get_concerns(candidate: dict, scores: dict) -> str:
    """
    Identify honest concerns for lower-ranked candidates.
    """
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]
    concerns = []

    # Experience outside ideal band
    yoe = profile.get("years_of_experience", 0)
    if yoe < 4 or yoe > 10:
        concerns.append(
            f"experience ({yoe:.1f}yr) outside ideal 5-9yr band"
        )

    # Low response rate
    rr = signals.get("recruiter_response_rate", 0)
    if rr < 0.25:
        concerns.append(f"low response rate ({rr:.0%})")

    # Not in India
    if profile.get("country") != PREFERRED_COUNTRY:
        concerns.append(f"located outside India ({profile.get('country', 'unknown')})")

    # IT Services / Consulting background
    industry = profile.get("current_industry", "")
    if industry in ("IT Services", "Consulting"):
        concerns.append(f"{industry} background")

    # Long notice period
    notice = signals.get("notice_period_days", 60)
    if notice > 90:
        concerns.append(f"long notice period ({notice} days)")

    # Low career trajectory score
    if scores.get("career_trajectory", 0) < 0.3:
        concerns.append("limited AI/ML content in career history")

    return "; ".join(concerns[:2]) if concerns else ""
