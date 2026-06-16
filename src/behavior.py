"""
Behavioral Signal Modifier

Stage 3 of the pipeline: multiplicative modifier applied to the base score
using the 23 Redrob engagement/behavioral signals.

Key insight from the JD:
  "A perfect-on-paper candidate who hasn't logged in for 6 months and has a
   5% recruiter response rate is, for hiring purposes, not actually available."

The modifier ranges from ~0.15 (terrible engagement) to ~1.35 (excellent
engagement), applied multiplicatively to the base score.
"""

from datetime import datetime, date


# Reference date for recency calculations
REFERENCE_DATE = date(2026, 6, 15)


def compute_behavioral_modifier(candidate: dict) -> float:
    """
    Compute a multiplicative modifier based on behavioral signals.

    Returns:
        float in range ~[0.15, 1.35]
    """
    signals = candidate["redrob_signals"]

    # -----------------------------------------------------------------
    # 1. Recency: When did they last log in?
    # -----------------------------------------------------------------
    try:
        last_active = datetime.strptime(
            signals["last_active_date"], "%Y-%m-%d"
        ).date()
        days_since = (REFERENCE_DATE - last_active).days
    except (ValueError, KeyError):
        days_since = 365  # Assume inactive if missing

    if days_since <= 7:
        recency = 1.0
    elif days_since <= 30:
        recency = 0.95
    elif days_since <= 90:
        recency = 0.85
    elif days_since <= 180:
        recency = 0.70
    elif days_since <= 365:
        recency = 0.50
    else:
        recency = 0.30

    # -----------------------------------------------------------------
    # 2. Recruiter response rate: Will they reply to outreach?
    # -----------------------------------------------------------------
    response_rate = signals.get("recruiter_response_rate", 0.0)
    # Map 0-1 to 0.5-1.0 (even low responders aren't worthless)
    response_mod = 0.50 + 0.50 * response_rate

    # -----------------------------------------------------------------
    # 3. Open to work flag
    # -----------------------------------------------------------------
    open_to_work = signals.get("open_to_work_flag", False)
    open_mod = 1.0 if open_to_work else 0.88

    # -----------------------------------------------------------------
    # 4. Interview completion rate: Are they reliable?
    # -----------------------------------------------------------------
    interview_rate = signals.get("interview_completion_rate", 0.5)
    interview_mod = 0.70 + 0.30 * interview_rate

    # -----------------------------------------------------------------
    # 5. Profile completeness
    # -----------------------------------------------------------------
    completeness = signals.get("profile_completeness_score", 50) / 100.0
    completeness_mod = 0.65 + 0.35 * completeness

    # -----------------------------------------------------------------
    # 6. Notice period (JD prefers <30 days)
    # -----------------------------------------------------------------
    notice = signals.get("notice_period_days", 60)
    if notice <= 15:
        notice_mod = 1.0
    elif notice <= 30:
        notice_mod = 0.95
    elif notice <= 60:
        notice_mod = 0.88
    elif notice <= 90:
        notice_mod = 0.78
    else:
        notice_mod = 0.65

    # -----------------------------------------------------------------
    # 7. GitHub activity (positive signal for an AI role)
    # -----------------------------------------------------------------
    github = signals.get("github_activity_score", -1)
    if github < 0:
        github_mod = 1.0  # No GitHub = neutral (don't penalize)
    elif github >= 70:
        github_mod = 1.10
    elif github >= 40:
        github_mod = 1.05
    elif github >= 10:
        github_mod = 1.0
    else:
        github_mod = 0.98

    # -----------------------------------------------------------------
    # 8. Verification status (trust signal)
    # -----------------------------------------------------------------
    verified_count = sum([
        signals.get("verified_email", False),
        signals.get("verified_phone", False),
        signals.get("linkedin_connected", False),
    ])
    verify_mod = 0.90 + 0.033 * verified_count  # 0.90 to ~1.0

    # -----------------------------------------------------------------
    # 9. Saved by recruiters (market demand signal)
    # -----------------------------------------------------------------
    saved = signals.get("saved_by_recruiters_30d", 0)
    saved_mod = 1.0 + min(saved / 60.0, 0.08)

    # -----------------------------------------------------------------
    # 10. Response time (faster = better)
    # -----------------------------------------------------------------
    avg_response_hours = signals.get("avg_response_time_hours", 100)
    if avg_response_hours <= 12:
        response_time_mod = 1.05
    elif avg_response_hours <= 48:
        response_time_mod = 1.0
    elif avg_response_hours <= 96:
        response_time_mod = 0.95
    else:
        response_time_mod = 0.90

    # -----------------------------------------------------------------
    # Combine multiplicatively
    # -----------------------------------------------------------------
    modifier = (
        recency
        * response_mod
        * open_mod
        * interview_mod
        * completeness_mod
        * notice_mod
        * github_mod
        * verify_mod
        * saved_mod
        * response_time_mod
    )

    return round(modifier, 6)


def get_behavioral_summary(candidate: dict) -> dict:
    """
    Return a human-readable summary of behavioral signals for debugging.
    """
    signals = candidate["redrob_signals"]

    try:
        last_active = datetime.strptime(
            signals["last_active_date"], "%Y-%m-%d"
        ).date()
        days_since = (REFERENCE_DATE - last_active).days
    except (ValueError, KeyError):
        days_since = -1

    return {
        "days_since_active": days_since,
        "response_rate": signals.get("recruiter_response_rate", 0),
        "open_to_work": signals.get("open_to_work_flag", False),
        "interview_completion": signals.get("interview_completion_rate", 0),
        "profile_completeness": signals.get("profile_completeness_score", 0),
        "notice_period_days": signals.get("notice_period_days", 0),
        "github_score": signals.get("github_activity_score", -1),
        "verified_count": sum([
            signals.get("verified_email", False),
            signals.get("verified_phone", False),
            signals.get("linkedin_connected", False),
        ]),
        "saved_by_recruiters": signals.get("saved_by_recruiters_30d", 0),
        "modifier": compute_behavioral_modifier(candidate),
    }
