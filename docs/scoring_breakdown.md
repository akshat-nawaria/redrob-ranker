"""
Scoring Breakdown Documentation

Detailed explanation of how each scoring axis works, with examples.
"""

# ===========================================================================
# TITLE/ROLE FIT (Weight: 25%)
# ===========================================================================
#
# Maps candidate titles to relevance scores for "Senior AI Engineer":
#
#   Title                          Score    Rationale
#   ──────────────────────────────  ─────   ──────────────────────────────
#   AI Engineer                    1.00     Direct match
#   Senior ML Engineer             0.98     Near-identical role
#   ML Engineer                    0.95     Core ML role
#   Data Scientist                 0.80     Strong ML overlap
#   Data Engineer                  0.72     Adjacent data infrastructure
#   Backend Engineer               0.68     Systems engineering foundation
#   Software Engineer              0.63     General engineering
#   Full Stack Developer           0.52     Too broad, less ML focus
#   Cloud Engineer                 0.48     Infrastructure only
#   Business Analyst               0.12     Weak tech connection
#   HR Manager                     0.03     Non-tech role
#
# Formula: 70% × current_title + 30% × best_past_title
# Rationale: Past titles matter — someone who was an ML Engineer and is
# now a Backend Engineer still has ML experience.

# ===========================================================================
# SKILL RELEVANCE (Weight: 20%) — Trust-Weighted
# ===========================================================================
#
# Key insight: ~12K candidates have each skill (near-uniform distribution).
# Skill presence alone means nothing. We use:
#
#   trust = 0.40 × duration_trust + 0.30 × endorsement_trust + 0.30 × proficiency
#
# Where:
#   duration_trust = min(duration_months / 36, 1.0)
#   endorsement_trust = min(endorsements / 25, 1.0)
#   proficiency = {beginner: 0.2, intermediate: 0.5, advanced: 0.75, expert: 1.0}
#
# CRITICAL PENALTY:
#   If proficiency ∈ {advanced, expert} AND duration < 6 months → trust = 0.08
#   This catches keyword stuffers who claim "expert" with 0 experience.
#
# Each skill's contribution = SKILL_WEIGHTS[skill_name] × trust
# Final score = min(total_weighted / 18.0, 1.0) + coverage_bonus

# ===========================================================================
# CAREER TRAJECTORY (Weight: 15%)
# ===========================================================================
#
# NLP-style keyword matching on career descriptions. Three categories:
#
# HIGH SIGNAL (×3): ranking system, recommendation system, retrieval,
#   embeddings, deployed model, evaluation framework, fine-tuning, etc.
#
# MEDIUM SIGNAL (×1): python, data science, deep learning, transformer,
#   api, backend, distributed, spark, etc.
#
# NEGATIVE SIGNAL (×-2): customer support, sales, marketing campaign,
#   accounting, hr process, mechanical engineering, cad, etc.
#
# Additional bonuses:
#   +0.12 for product company experience
#   +0.08 for career growth (senior/lead titles)
#   +0.05 for company size diversity
#   -0.10 for job hopping (<15 months average)

# ===========================================================================
# EXPERIENCE BAND (Weight: 12%)
# ===========================================================================
#
#   Years    Score    Notes
#   ──────   ─────   ────────────────────
#   5.0-9.0  1.00    Sweet spot per JD
#   4.0-5.0  0.70-1.00  Linear ramp
#   9.0-12.0 0.70-1.00  Gentle decay
#   3.0-4.0  0.40-0.70  Below ideal
#   12.0-15.0 0.25-0.70  Above ideal
#   2.0-3.0  0.20-0.40  Junior
#   <2 / >15 0.05    Hard filter usually catches these

# ===========================================================================
# BEHAVIORAL MODIFIER (Multiplicative, not additive)
# ===========================================================================
#
# 10 signals combined multiplicatively:
#
#   Signal                   Range        Effect
#   ──────────────────────   ────────     ──────────────────
#   Recency (last active)    0.30-1.00    Inactive = severe penalty
#   Response rate            0.50-1.00    Low responders penalized
#   Open to work             0.88-1.00    Not looking = small penalty
#   Interview completion     0.70-1.00    No-shows penalized
#   Profile completeness     0.65-1.00    Incomplete profiles penalized
#   Notice period            0.65-1.00    >90 days = penalty
#   GitHub activity          0.98-1.10    Active GitHub = small bonus
#   Verification status      0.90-1.00    Verified = trust bonus
#   Saved by recruiters      1.00-1.08    Market demand signal
#   Response time            0.90-1.05    Fast responders bonus
#
# Combined range: ~0.15 (worst) to ~1.35 (best)
# This means an inactive candidate's score is cut to ~15% of base.
