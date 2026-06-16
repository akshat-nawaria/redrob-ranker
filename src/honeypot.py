"""
Honeypot Detection Module

Detects ~80 candidates with subtly impossible profiles in the dataset.
Honeypots are identified through internal consistency checks:
- Expert skills with zero duration
- Career timelines that don't add up
- Assessment scores contradicting proficiency claims
- Endorsement/connection anomalies

If >10% of our top 100 are honeypots, we're disqualified.
"""

from datetime import datetime


def detect_honeypot_signals(candidate: dict) -> list[str]:
    """
    Returns a list of red-flag signals found in the candidate profile.
    Multiple signals = likely honeypot.
    """
    signals = []
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    profile = candidate["profile"]
    redrob = candidate["redrob_signals"]
    assessments = redrob.get("skill_assessment_scores", {})

    # -------------------------------------------------------------------------
    # Check 1: Expert/advanced proficiency with near-zero duration
    # A real expert has used the skill for at least 6-12 months.
    # -------------------------------------------------------------------------
    zero_duration_advanced = 0
    for s in skills:
        prof = s.get("proficiency", "beginner")
        dur = s.get("duration_months", 0)
        if prof in ("expert", "advanced") and dur <= 2:
            zero_duration_advanced += 1

    if zero_duration_advanced >= 3:
        signals.append(f"expert_zero_duration({zero_duration_advanced} skills)")

    # -------------------------------------------------------------------------
    # Check 2: Too many expert skills — unrealistic breadth
    # -------------------------------------------------------------------------
    expert_count = sum(1 for s in skills if s.get("proficiency") == "expert")
    if expert_count >= 8:
        signals.append(f"too_many_expert_skills({expert_count})")

    # -------------------------------------------------------------------------
    # Check 3: Career duration exceeds claimed experience significantly
    # -------------------------------------------------------------------------
    total_career_months = sum(j.get("duration_months", 0) for j in career)
    claimed_yoe = profile.get("years_of_experience", 0)
    # Allow 3 years of overlap tolerance (parallel roles, rounding, etc.)
    if total_career_months > (claimed_yoe + 3) * 12 and claimed_yoe > 0:
        signals.append(
            f"inflated_experience(career={total_career_months}mo, "
            f"claimed={claimed_yoe}yr)"
        )

    # -------------------------------------------------------------------------
    # Check 4: Impossibly long tenure at a single company
    # -------------------------------------------------------------------------
    for job in career:
        if job.get("duration_months", 0) > 200:  # 16+ years at one company
            # Only flag if total experience doesn't support it
            if claimed_yoe < job["duration_months"] / 12 - 2:
                signals.append(
                    f"impossible_tenure({job['company']}, "
                    f"{job['duration_months']}mo)"
                )

    # -------------------------------------------------------------------------
    # Check 5: Assessment scores drastically contradict proficiency
    # -------------------------------------------------------------------------
    contradictions = 0
    for s in skills:
        skill_name = s["name"]
        if skill_name in assessments:
            score = assessments[skill_name]
            prof = s.get("proficiency", "beginner")
            # Expert/advanced claiming but bombed the assessment
            if prof == "expert" and score < 15:
                contradictions += 1
            elif prof == "advanced" and score < 10:
                contradictions += 1

    if contradictions >= 2:
        signals.append(f"assessment_contradiction({contradictions} skills)")

    # -------------------------------------------------------------------------
    # Check 6: High endorsements with extremely low connections
    # You can't have 200 endorsements with 5 connections
    # -------------------------------------------------------------------------
    endorsements = redrob.get("endorsements_received", 0)
    connections = redrob.get("connection_count", 0)
    if endorsements > 80 and connections < 15:
        signals.append(
            f"endorsement_anomaly(endorsements={endorsements}, "
            f"connections={connections})"
        )

    # -------------------------------------------------------------------------
    # Check 7: Skill endorsements wildly exceed total endorsements
    # -------------------------------------------------------------------------
    total_skill_endorsements = sum(s.get("endorsements", 0) for s in skills)
    if total_skill_endorsements > 0 and endorsements > 0:
        if total_skill_endorsements > endorsements * 20 and total_skill_endorsements > 200:
            signals.append(
                f"skill_endorsement_inflation("
                f"skill_total={total_skill_endorsements}, "
                f"profile_total={endorsements})"
            )

    # -------------------------------------------------------------------------
    # Check 8: Experience years vs education timeline is impossible
    # -------------------------------------------------------------------------
    education = candidate.get("education", [])
    if education:
        earliest_end = min(
            (e.get("end_year", 2030) for e in education), default=2030
        )
        # If they graduated in 2022 but claim 15 years of experience...
        if earliest_end > 2000:
            max_possible_yoe = 2026 - earliest_end
            if claimed_yoe > max_possible_yoe + 4:  # 4-year tolerance
                signals.append(
                    f"impossible_yoe_vs_education("
                    f"claimed={claimed_yoe}yr, grad={earliest_end}, "
                    f"max_possible~{max_possible_yoe}yr)"
                )

    return signals


def is_honeypot(candidate: dict, threshold: int = 2) -> bool:
    """
    Returns True if the candidate has enough red-flag signals to be
    considered a honeypot.

    Args:
        candidate: Full candidate dict from JSONL.
        threshold: Minimum number of signals to flag as honeypot. Default 2.

    Returns:
        True if likely honeypot.
    """
    signals = detect_honeypot_signals(candidate)
    return len(signals) >= threshold


def get_honeypot_report(candidate: dict) -> dict:
    """
    Returns a detailed report for debugging/analysis.
    """
    signals = detect_honeypot_signals(candidate)
    return {
        "candidate_id": candidate["candidate_id"],
        "is_honeypot": len(signals) >= 2,
        "signal_count": len(signals),
        "signals": signals,
    }
