"""
Hard Filters Module

Stage 1 of the pipeline: deterministic elimination of obviously unfit candidates
before any scoring happens. This reduces the candidate pool from 100K to ~10-20K.

Filters are derived directly from the JD's explicit disqualifiers:
1. Honeypot detection
2. Experience band (too junior or too senior)
3. Consulting-only career
4. Non-tech title with no AI/ML career content
5. Domain mismatch (pure CV/speech/robotics without NLP/IR)
"""

from src.honeypot import is_honeypot
from src.jd_profile import (
    CONSULTING_COMPANIES,
    EXPERIENCE_HARD_MAX,
    EXPERIENCE_HARD_MIN,
    NON_TECH_TITLES,
    BORDERLINE_TITLES,
)


def passes_hard_filters(candidate: dict) -> tuple[bool, str]:
    """
    Determines whether a candidate should even be scored.

    Returns:
        (passes, reason) — if passes=False, reason explains why.
    """
    profile = candidate["profile"]
    career = candidate.get("career_history", [])

    # -----------------------------------------------------------------
    # Filter 1: Honeypot check (MOST CRITICAL — disqualification risk)
    # -----------------------------------------------------------------
    if is_honeypot(candidate):
        return False, "honeypot_detected"

    # -----------------------------------------------------------------
    # Filter 2: Experience band
    # JD says 5-9 ideal, but we use generous bounds for filtering.
    # Scoring handles the nuance.
    # -----------------------------------------------------------------
    yoe = profile.get("years_of_experience", 0)
    if yoe < EXPERIENCE_HARD_MIN:
        return False, f"too_junior({yoe:.1f}yr)"
    if yoe > EXPERIENCE_HARD_MAX:
        return False, f"too_senior({yoe:.1f}yr)"

    # -----------------------------------------------------------------
    # Filter 3: Entire career at consulting companies
    # JD: "People who have only worked at consulting firms in their
    #      entire career" — explicit disqualifier.
    # But: "if you're currently at one but have prior product-company
    #       experience, that's fine"
    # -----------------------------------------------------------------
    if len(career) >= 2:
        all_consulting = all(
            any(
                c in job.get("company", "").lower()
                for c in CONSULTING_COMPANIES
            )
            for job in career
        )
        if all_consulting:
            return False, "consulting_only_career"

    # -----------------------------------------------------------------
    # Filter 4: Non-tech title with no AI/ML content in career
    # The dataset has Marketing Managers with AI skills (trap).
    # But: some non-tech-titled people have real ML work in descriptions.
    # -----------------------------------------------------------------
    title = profile.get("current_title", "")
    if title in NON_TECH_TITLES:
        # Scan career descriptions for AI/ML substance
        has_ai_career = _has_ai_career_content(career)
        if not has_ai_career:
            return False, f"non_tech_title_no_ai_career({title})"

    # -----------------------------------------------------------------
    # Filter 5: Pure CV/speech/robotics without NLP/IR exposure
    # JD: "people whose primary expertise is computer vision, speech,
    #       or robotics without significant NLP/IR exposure"
    # Only filter if ALL career descriptions are CV/speech and NONE
    # mention NLP/IR/search/ranking/retrieval.
    # -----------------------------------------------------------------
    if _is_pure_cv_speech_robotics(candidate):
        return False, "cv_speech_only_no_nlp_ir"

    return True, "passed"


def _has_ai_career_content(career: list[dict]) -> bool:
    """
    Check if any career description mentions AI/ML/ranking/retrieval work.
    This is what separates keyword-stuffed profiles from genuine candidates
    whose titles don't reflect their actual work.
    """
    ai_keywords = [
        "machine learning", "ml ", "ml,", "deep learning", "neural",
        "embedding", "nlp", "natural language", "ranking", "recommendation",
        "retrieval", "search", "ai ", "ai,", "ai/ml", "data science",
        "model training", "model deploy", "inference", "classification",
        "prediction", "clustering", "feature engineering",
        "tensorflow", "pytorch", "scikit", "xgboost",
        "transformer", "bert", "gpt", "llm",
    ]

    all_desc = " ".join(
        job.get("description", "").lower() for job in career
    )

    match_count = sum(1 for kw in ai_keywords if kw in all_desc)
    return match_count >= 3  # Need at least 3 distinct AI-related terms


def _is_pure_cv_speech_robotics(candidate: dict) -> bool:
    """
    Check if candidate's entire career is CV/speech/robotics
    WITHOUT any NLP/IR exposure.
    """
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])

    # CV/speech indicators
    cv_speech_skills = {
        "Image Classification", "Object Detection", "Computer Vision",
        "Speech Recognition", "TTS", "OpenCV", "YOLO",
        "Image Segmentation", "Face Recognition",
    }

    # NLP/IR indicators
    nlp_ir_skills = {
        "NLP", "Natural Language Processing", "Information Retrieval",
        "Text Classification", "Sentiment Analysis", "BERT",
        "Transformers", "Hugging Face", "sentence-transformers",
        "Elasticsearch", "FAISS", "Milvus", "Pinecone",
        "RAG", "Search", "Ranking", "Recommendation Systems",
        "spaCy", "NLTK", "Gensim", "Word2Vec",
    }

    candidate_skills = {s["name"] for s in skills}
    has_cv_speech = bool(candidate_skills & cv_speech_skills)
    has_nlp_ir = bool(candidate_skills & nlp_ir_skills)

    # Also check career descriptions
    all_desc = " ".join(
        job.get("description", "").lower() for job in career
    )
    nlp_ir_in_career = any(
        kw in all_desc
        for kw in [
            "nlp", "natural language", "search", "retrieval",
            "ranking", "recommendation", "information retrieval",
            "text", "embedding",
        ]
    )

    # Only filter if they have CV/speech skills but NO NLP/IR at all
    return has_cv_speech and not has_nlp_ir and not nlp_ir_in_career
