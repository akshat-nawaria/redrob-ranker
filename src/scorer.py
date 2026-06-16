"""
Multi-Axis Scoring Engine

Stage 2 of the pipeline: compute a base score for each surviving candidate
across 8 orthogonal axes. Each axis produces a 0-1 score, combined via
weighted sum.

Axes:
  1. Title/Role Fit        (weight 0.25)
  2. Skill Relevance       (weight 0.20)
  3. Career Trajectory     (weight 0.15)
  4. Experience Band       (weight 0.12)
  5. Domain/Industry       (weight 0.10)
  6. Location Fit          (weight 0.08)
  7. Education Relevance   (weight 0.05)
  8. Certification Bonus   (weight 0.05)
"""

from src.jd_profile import (
    TITLE_RELEVANCE,
    SKILL_WEIGHTS,
    HIGH_SIGNAL_CAREER_KEYWORDS,
    MEDIUM_SIGNAL_CAREER_KEYWORDS,
    NEGATIVE_CAREER_KEYWORDS,
    INDUSTRY_RELEVANCE,
    PREFERRED_CITIES,
    PREFERRED_COUNTRY,
    EDUCATION_FIELD_HIGH,
    EDUCATION_FIELD_MEDIUM,
    EDUCATION_FIELD_LOW,
    CERTIFICATION_RELEVANCE,
    CONSULTING_COMPANIES,
)

# Axis weights — must sum to 1.0
AXIS_WEIGHTS = {
    "title_fit": 0.25,
    "skill_relevance": 0.20,
    "career_trajectory": 0.15,
    "experience_band": 0.12,
    "domain_industry": 0.10,
    "location_fit": 0.08,
    "education": 0.05,
    "certifications": 0.05,
}


def compute_all_scores(candidate: dict) -> dict:
    """
    Compute scores for all 8 axes.

    Returns:
        dict mapping axis name → score (0-1)
    """
    return {
        "title_fit": _score_title_fit(candidate),
        "skill_relevance": _score_skill_relevance(candidate),
        "career_trajectory": _score_career_trajectory(candidate),
        "experience_band": _score_experience_band(candidate),
        "domain_industry": _score_domain_industry(candidate),
        "location_fit": _score_location_fit(candidate),
        "education": _score_education(candidate),
        "certifications": _score_certifications(candidate),
    }


def compute_base_score(scores: dict) -> float:
    """
    Weighted combination of axis scores.
    """
    total = sum(
        AXIS_WEIGHTS[axis] * scores[axis]
        for axis in AXIS_WEIGHTS
    )
    return round(total, 6)


# =========================================================================
# Axis 1: Title/Role Fit
# =========================================================================

def _score_title_fit(candidate: dict) -> float:
    """
    Score based on current title + best historical title.
    Weight: 70% current, 30% best historical.
    """
    profile = candidate["profile"]
    career = candidate.get("career_history", [])

    current_title = profile.get("current_title", "")
    current_score = TITLE_RELEVANCE.get(current_title, 0.10)

    # Check historical titles
    past_scores = []
    for job in career:
        if not job.get("is_current", False):
            title = job.get("title", "")
            past_scores.append(TITLE_RELEVANCE.get(title, 0.10))

    best_past = max(past_scores) if past_scores else 0.0

    return min(0.70 * current_score + 0.30 * best_past, 1.0)


# =========================================================================
# Axis 2: Skill Relevance (with trust-weighting)
# =========================================================================

def _compute_skill_trust(skill: dict) -> float:
    """
    How much do we trust this skill claim?
    Cross-references proficiency with duration and endorsements.
    A skill claiming "expert" with 0 months and 0 endorsements gets penalized.
    """
    prof = skill.get("proficiency", "beginner")
    dur = skill.get("duration_months", 0)
    endorse = skill.get("endorsements", 0)

    # Duration trust (0-1), saturates at 36 months
    dur_trust = min(dur / 36.0, 1.0) if dur > 0 else 0.0

    # Endorsement trust (0-1), saturates at 25
    endorse_trust = min(endorse / 25.0, 1.0)

    # Proficiency baseline
    prof_map = {
        "beginner": 0.20,
        "intermediate": 0.50,
        "advanced": 0.75,
        "expert": 1.00,
    }
    prof_score = prof_map.get(prof, 0.20)

    # Consistency penalty: high proficiency + low duration = suspicious
    if prof in ("advanced", "expert") and dur < 6:
        return 0.08  # Nearly zero — likely keyword stuffing

    if prof == "expert" and dur < 12:
        return 0.15  # Still suspicious

    # Weighted combination
    trust = 0.40 * dur_trust + 0.30 * endorse_trust + 0.30 * prof_score
    return trust


def _score_skill_relevance(candidate: dict) -> float:
    """
    Score based on relevant skills weighted by JD importance and trust.
    """
    skills = candidate.get("skills", [])
    assessments = candidate["redrob_signals"].get("skill_assessment_scores", {})

    total_weighted = 0.0
    found_must_have_categories = set()

    for skill in skills:
        name = skill["name"]
        jd_weight = SKILL_WEIGHTS.get(name, 0.05)

        if jd_weight < 0.1:
            continue  # Skip irrelevant skills entirely

        trust = _compute_skill_trust(skill)

        # Assessment bonus: if they took and passed an assessment
        if name in assessments:
            assessment_score = assessments[name]
            if assessment_score >= 60:
                trust = min(trust * 1.3, 1.0)  # 30% boost for passing
            elif assessment_score < 20:
                trust *= 0.5  # Penalty for bombing it

        total_weighted += jd_weight * trust

        # Track must-have coverage
        if jd_weight >= 2.5:
            found_must_have_categories.add(name)

    # Normalize: max realistic score ~20-25 weighted units
    normalized = min(total_weighted / 18.0, 1.0)

    # Bonus for breadth of must-have coverage
    coverage_bonus = min(len(found_must_have_categories) * 0.03, 0.15)

    return min(normalized + coverage_bonus, 1.0)


# =========================================================================
# Axis 3: Career Trajectory
# =========================================================================

def _score_career_trajectory(candidate: dict) -> float:
    """
    Analyze career descriptions for actual AI/ML/ranking/retrieval work.
    Also considers: product company experience, career growth, job stability.
    """
    career = candidate.get("career_history", [])
    if not career:
        return 0.0

    all_desc = " ".join(
        job.get("description", "").lower() for job in career
    )

    # Keyword matching on career descriptions
    high_hits = sum(1 for kw in HIGH_SIGNAL_CAREER_KEYWORDS if kw in all_desc)
    med_hits = sum(1 for kw in MEDIUM_SIGNAL_CAREER_KEYWORDS if kw in all_desc)
    neg_hits = sum(1 for kw in NEGATIVE_CAREER_KEYWORDS if kw in all_desc)

    keyword_score = (high_hits * 3.0 + med_hits * 1.0 - neg_hits * 2.0)
    keyword_normalized = min(max(keyword_score / 20.0, 0.0), 0.70)

    # Product company bonus
    product_industries = {
        "Software", "Fintech", "E-commerce", "SaaS", "AI/ML",
        "EdTech", "AdTech", "HealthTech", "HealthTech AI",
        "Conversational AI", "AI Services", "Voice AI", "Gaming",
        "Insurance Tech", "Internet", "Media", "Food Delivery",
    }
    has_product = any(
        job.get("industry", "") in product_industries for job in career
    )
    product_bonus = 0.12 if has_product else 0.0

    # Career growth: title progression
    titles = [job.get("title", "").lower() for job in career]
    has_growth = any(
        kw in t for t in titles
        for kw in ["senior", "lead", "principal", "staff", "head", "director"]
    )
    growth_bonus = 0.08 if has_growth else 0.0

    # Job stability: penalize excessive hopping (JD mentions "title-chasers")
    if len(career) >= 3:
        avg_tenure_months = sum(
            j.get("duration_months", 0) for j in career
        ) / len(career)
        if avg_tenure_months < 15:  # Less than 1.25 years average
            stability_penalty = 0.10
        elif avg_tenure_months < 20:
            stability_penalty = 0.05
        else:
            stability_penalty = 0.0
    else:
        stability_penalty = 0.0

    # Company size diversity (startups + big co = well-rounded)
    company_sizes = {job.get("company_size", "") for job in career}
    small_co = company_sizes & {"1-10", "11-50", "51-200"}
    big_co = company_sizes & {"1001-5000", "5001-10000", "10001+"}
    diversity_bonus = 0.05 if (small_co and big_co) else 0.0

    total = (
        keyword_normalized
        + product_bonus
        + growth_bonus
        + diversity_bonus
        - stability_penalty
    )

    return min(max(total, 0.0), 1.0)


# =========================================================================
# Axis 4: Experience Band
# =========================================================================

def _score_experience_band(candidate: dict) -> float:
    """
    Gaussian-like scoring around the ideal 5-9 year band.
    """
    yoe = candidate["profile"].get("years_of_experience", 0)

    if 5.0 <= yoe <= 9.0:
        return 1.0
    elif 4.0 <= yoe < 5.0:
        return 0.70 + 0.30 * (yoe - 4.0)  # Linear ramp from 0.7 to 1.0
    elif 9.0 < yoe <= 12.0:
        return 1.0 - 0.10 * (yoe - 9.0)   # Gentle decay from 1.0 to 0.7
    elif 3.0 <= yoe < 4.0:
        return 0.40 + 0.30 * (yoe - 3.0)  # 0.4 to 0.7
    elif 12.0 < yoe <= 15.0:
        return 0.70 - 0.15 * (yoe - 12.0) # 0.7 to 0.25
    elif 2.0 <= yoe < 3.0:
        return 0.20 + 0.20 * (yoe - 2.0)  # 0.2 to 0.4
    else:
        return 0.05


# =========================================================================
# Axis 5: Domain/Industry Fit
# =========================================================================

def _score_domain_industry(candidate: dict) -> float:
    """
    Score based on current and past industry relevance.
    """
    profile = candidate["profile"]
    career = candidate.get("career_history", [])

    current_industry = profile.get("current_industry", "")
    current_score = INDUSTRY_RELEVANCE.get(current_industry, 0.08)

    # Best historical industry
    past_scores = [
        INDUSTRY_RELEVANCE.get(job.get("industry", ""), 0.08)
        for job in career
        if not job.get("is_current", False)
    ]
    best_past = max(past_scores) if past_scores else 0.08

    # 60% current, 40% best past
    return min(0.60 * current_score + 0.40 * best_past, 1.0)


# =========================================================================
# Axis 6: Location Fit
# =========================================================================

def _score_location_fit(candidate: dict) -> float:
    """
    Location scoring per JD preferences.
    """
    profile = candidate["profile"]
    location = profile.get("location", "").lower()
    country = profile.get("country", "")
    willing_relocate = candidate["redrob_signals"].get("willing_to_relocate", False)

    # Perfect: Pune or Noida
    if any(city in location for city in ["pune", "noida"]):
        return 1.0

    # Strong: Other preferred Indian cities
    if country == PREFERRED_COUNTRY:
        if any(city in location for city in PREFERRED_CITIES):
            return 0.82
        # India, other city, willing to relocate
        if willing_relocate:
            return 0.65
        # India, other city, won't relocate
        return 0.50

    # International, willing to relocate
    if willing_relocate:
        return 0.30

    # International, won't relocate
    return 0.15


# =========================================================================
# Axis 7: Education Relevance
# =========================================================================

def _score_education(candidate: dict) -> float:
    """
    Score based on field of study, institution tier, and degree level.
    """
    education = candidate.get("education", [])
    if not education:
        return 0.20  # No education data → neutral-low

    best_score = 0.0
    for edu in education:
        field = edu.get("field_of_study", "").lower()
        tier = edu.get("tier", "unknown")
        degree = edu.get("degree", "")

        # Field relevance
        if any(f in field for f in EDUCATION_FIELD_HIGH):
            field_score = 1.0
        elif any(f in field for f in EDUCATION_FIELD_MEDIUM):
            field_score = 0.75
        elif any(f in field for f in EDUCATION_FIELD_LOW):
            field_score = 0.45
        else:
            field_score = 0.10

        # Tier bonus
        tier_map = {
            "tier_1": 0.20,
            "tier_2": 0.10,
            "tier_3": 0.0,
            "tier_4": -0.05,
            "unknown": 0.0,
        }
        tier_bonus = tier_map.get(tier, 0.0)

        # Degree level bonus
        advanced_degrees = {"M.Tech", "M.Sc", "M.E.", "Ph.D", "MBA", "MS"}
        degree_bonus = 0.08 if degree in advanced_degrees else 0.0

        edu_score = min(max(field_score + tier_bonus + degree_bonus, 0.0), 1.0)
        best_score = max(best_score, edu_score)

    return best_score


# =========================================================================
# Axis 8: Certification Bonus
# =========================================================================

def _score_certifications(candidate: dict) -> float:
    """
    Score based on relevant certifications.
    """
    certs = candidate.get("certifications", [])
    if not certs:
        return 0.0

    total = 0.0
    for cert in certs:
        cert_name = cert.get("name", "").lower()
        for pattern, score in CERTIFICATION_RELEVANCE.items():
            if pattern in cert_name:
                total += score
                break

    return min(total / 1.5, 1.0)  # Normalize — 1-2 good certs = full score
