# Redrob Intelligent Candidate Ranking System

> **Beyond Keywords** — An AI system that ranks candidates the way a great recruiter would.

Built for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**.

## 🎯 Approach

Multi-stage rule-based ranker with trust-weighted skill verification and behavioral signal modifiers. The system reads the JD as a recruiter would — understanding disqualifiers, career trajectory, and engagement signals — not just matching keywords.

### Architecture

```
candidates.jsonl (100K)
        │
        ▼
┌─── Stage 1: Hard Filters ──────────────────────────┐
│  Honeypot detection, title/experience filtering,     │
│  consulting-only career elimination                  │
│  → ~85K eliminated, ~15K survive                    │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─── Stage 2: Multi-Axis Scoring ─────────────────────┐
│  8 axes: title fit, skill relevance (trust-weighted),│
│  career trajectory, experience band, domain/industry,│
│  location, education, certifications                 │
│  → Base score (0-1)                                  │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─── Stage 3: Behavioral Modifier ────────────────────┐
│  10 signals: recency, response rate, notice period,  │
│  GitHub activity, interview completion, etc.         │
│  → Multiplicative modifier (0.15 - 1.35)            │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─── Stage 4: Rank + Explain ─────────────────────────┐
│  Sort by final_score, take top 100, generate         │
│  per-candidate reasoning grounded in profile data    │
│  → submission.csv                                    │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **No embeddings / No LLMs during ranking** — The pipeline runs on pure Python with zero external dependencies, finishing in <60s on CPU.
2. **Trust-weighted skills** — Skills with 0 months duration or 0 endorsements claiming "expert" proficiency are heavily penalized (catches keyword stuffers).
3. **Career description analysis** — Keyword matching on career history descriptions to find candidates who actually built ML/ranking/retrieval systems, even if their title is "Backend Engineer."
4. **Honeypot detection** — 8 consistency checks catching impossible profiles (expert in 10 skills with 0 duration, career timelines that exceed claimed experience, etc.).
5. **Behavioral signals as multipliers** — A perfect-on-paper candidate with 5% response rate is down-weighted multiplicatively.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- No external packages required for ranking (stdlib only)

### Run the Ranker

```bash
# Produce submission.csv from candidates.jsonl
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### Validate Submission

```bash
python validate_submission.py submission.csv
```

### Run Analysis

```bash
# Analyze score distribution and quality metrics
python analysis/score_analysis.py -s ./submission.csv -c ./candidates.jsonl

# Compare against keyword-matching baseline
python analysis/baseline_comparison.py -c ./candidates.jsonl
```

### Run Streamlit Demo

```bash
pip install streamlit
streamlit run app.py
```

### Docker

```bash
docker build -t redrob-ranker .
docker run -v /path/to/data:/data -v /path/to/output:/output redrob-ranker
```

## 📁 Project Structure

```
redrob-ranker/
├── rank.py                      # Main entry point
├── src/
│   ├── __init__.py
│   ├── jd_profile.py            # JD requirements as data structures
│   ├── honeypot.py              # Honeypot detection (8 checks)
│   ├── filters.py               # Hard filter module
│   ├── scorer.py                # 8-axis scoring engine
│   ├── behavior.py              # Behavioral signal modifier
│   ├── explain.py               # Reasoning generation
│   └── utils.py                 # Shared utilities
├── analysis/
│   ├── score_analysis.py        # Submission quality analysis
│   └── baseline_comparison.py   # Keyword baseline comparison
├── app.py                       # Streamlit sandbox app
├── Dockerfile                   # Docker reproducibility
├── requirements.txt             # Dependencies (minimal)
├── submission_metadata.yaml     # Hackathon metadata
├── submission.csv               # Generated output
└── README.md                    # This file
```

## 📊 Scoring Formula

```
Final Score = Base Score × Behavioral Modifier

Base Score = Σ(weight_i × axis_score_i)

Weights:
  Title/Role Fit:        25%
  Skill Relevance:       20%  (trust-weighted)
  Career Trajectory:     15%  (NLP on descriptions)
  Experience Band:       12%  (Gaussian around 5-9yr)
  Domain/Industry:       10%
  Location Fit:           8%
  Education:              5%
  Certifications:         5%

Behavioral Modifier = Π(signal_j)
  Signals: recency, response rate, open-to-work, interview completion,
           profile completeness, notice period, GitHub activity,
           verification, recruiter saves, response time
```

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Runtime (100K candidates) | ~30-45 seconds |
| Peak memory | ~3-4 GB |
| External dependencies | None (stdlib only) |
| GPU required | No |
| Network required | No |

## 🛡️ Trap Avoidance

- **Keyword stuffing**: Trust-weighted skill scoring penalizes high-proficiency + low-duration combos
- **Non-tech titles**: Hard filter eliminates HR Managers, Accountants, etc. unless career shows AI work
- **Consulting-only**: Entire career at TCS/Infosys/Wipro = filtered
- **Honeypots**: 8 consistency checks detect impossible profiles
- **Inactive candidates**: Behavioral modifier down-weights unresponsive/inactive profiles

## 📝 License

Built for the Redrob Hackathon. All rights reserved.
