# Architecture Documentation

## System Overview

The Redrob Intelligent Candidate Ranking System is a multi-stage pipeline
designed to rank 100K candidates for a Senior AI Engineer role. It avoids
the common pitfall of keyword matching by analyzing career trajectories,
applying trust-weighted skill scoring, and incorporating behavioral signals.

## Pipeline Stages

### Stage 1: Hard Filters (Rule-Based)

**Purpose:** Eliminate obviously unfit candidates before scoring.

**Filters applied:**
1. **Honeypot Detection** — 8 consistency checks identify impossible profiles
2. **Experience Band** — Remove candidates <2 years or >15 years
3. **Consulting-Only Career** — Entire career at TCS/Infosys/Wipro/etc.
4. **Non-Tech Titles** — HR Manager, Accountant, etc. unless career descriptions show AI work
5. **CV/Speech-Only** — Pure computer vision/speech without NLP/IR exposure

**Expected reduction:** 100K → ~10-15K candidates

### Stage 2: Multi-Axis Scoring (Feature-Engineered)

**Purpose:** Score each surviving candidate across 8 orthogonal dimensions.

Each axis produces a score in [0, 1]:

| Axis | Weight | What It Measures |
|------|--------|-----------------|
| Title/Role Fit | 25% | How close is current+past title to "Senior AI Engineer" |
| Skill Relevance | 20% | JD-weighted skills with trust verification |
| Career Trajectory | 15% | AI/ML/ranking keywords in career descriptions |
| Experience Band | 12% | Gaussian scoring centered on 5-9 year sweet spot |
| Domain/Industry | 10% | AI/ML > Software > IT Services > Manufacturing |
| Location Fit | 8% | Pune/Noida > Indian cities > India > International |
| Education | 5% | CS/ML field + institution tier + degree level |
| Certifications | 5% | Relevant ML/cloud certifications |

### Stage 3: Behavioral Modifier (Signal-Based)

**Purpose:** Adjust for real-world hirability using platform engagement data.

**Signals used (10 total):**
- Recency (last active date)
- Recruiter response rate
- Open-to-work flag
- Interview completion rate
- Profile completeness
- Notice period
- GitHub activity score
- Verification status (email/phone/LinkedIn)
- Saved by recruiters (market demand)
- Average response time

**Output:** Multiplicative modifier in ~[0.15, 1.35]

### Stage 4: Rank + Explain

**Purpose:** Sort by final score, select top 100, generate reasoning.

**Reasoning quality constraints:**
- Every fact references actual profile data
- No two candidates get identical reasoning
- Lower-ranked candidates get honest concerns
- Tone matches rank position

## Key Innovation: Trust-Weighted Skill Scoring

The dataset distributes skills near-uniformly (~12K candidates per skill).
This means skill presence alone is meaningless. Our trust multiplier
cross-references:
- **Duration** — How long they've used the skill
- **Endorsements** — How many peers validated it
- **Proficiency claim** — Consistency with duration
- **Assessment scores** — Platform-verified scores

A skill claiming "expert" with 0 months and 0 endorsements gets ~0.08 trust.
A skill with 36+ months, 25+ endorsements, and passing assessment gets ~1.0.

## Scoring Formula

```
Final_Score = Base_Score × Behavioral_Modifier

Base_Score = Σ(weight_i × axis_score_i) for i in [1..8]

Behavioral_Modifier = Π(signal_modifier_j) for j in [1..10]
```
