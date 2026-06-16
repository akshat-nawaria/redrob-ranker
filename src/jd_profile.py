"""
Job Description Profile — Structured extraction of the Redrob Senior AI Engineer JD.

This module encodes the JD as a Python data structure so every other module can
reference it without re-parsing.  Since the challenge has exactly ONE JD, we
hard-code it after careful reading rather than building a generic parser.

Key insight: the JD is unusually specific about disqualifiers, making rule-based
filtering extremely powerful here.
"""

# ---------------------------------------------------------------------------
# Must-have skills (hard requirements from the JD)
# Each key is a *requirement category*, values are surface-form keywords that
# indicate the candidate has this capability.
# ---------------------------------------------------------------------------
MUST_HAVE_SKILLS = {
    "embeddings_retrieval": [
        "sentence-transformers", "sentence transformers", "BGE", "E5",
        "OpenAI embeddings", "embeddings", "embedding", "dense retrieval",
        "semantic search", "vector search", "bi-encoder",
    ],
    "vector_db_hybrid_search": [
        "Pinecone", "Weaviate", "Qdrant", "Milvus", "FAISS", "faiss",
        "Elasticsearch", "OpenSearch", "Vespa", "Chroma", "ChromaDB",
        "vector database", "vector db", "hybrid search", "ANN",
        "approximate nearest neighbor",
    ],
    "python": [
        "Python",
    ],
    "ranking_eval_frameworks": [
        "NDCG", "MRR", "MAP", "precision", "recall", "F1",
        "A/B test", "ab test", "ranking evaluation", "evaluation framework",
        "offline evaluation", "online evaluation", "information retrieval",
    ],
}

# ---------------------------------------------------------------------------
# Nice-to-have skills (boost but don't require)
# ---------------------------------------------------------------------------
NICE_TO_HAVE_SKILLS = {
    "llm_finetuning": [
        "LoRA", "QLoRA", "PEFT", "fine-tuning", "fine tuning", "finetuning",
        "adapter", "SFT", "RLHF", "DPO",
    ],
    "learning_to_rank": [
        "XGBoost", "xgboost", "LambdaMART", "learning-to-rank", "learning to rank",
        "LTR", "LightGBM", "CatBoost", "gradient boosting",
    ],
    "hrtech_marketplace": [
        "HR-tech", "hrtech", "recruiting", "recruitment", "ATS",
        "applicant tracking", "talent", "marketplace", "job matching",
    ],
    "distributed_inference": [
        "distributed systems", "distributed", "inference optimization",
        "model serving", "TensorRT", "ONNX", "triton", "scaling",
        "horizontal scaling", "load balancing",
    ],
    "opensource_contributions": [
        "open-source", "open source", "contributor", "maintainer",
        "GitHub", "github", "pull request",
    ],
}

# ---------------------------------------------------------------------------
# Experience configuration
# ---------------------------------------------------------------------------
EXPERIENCE_SWEET_SPOT = (5.0, 9.0)     # Ideal range
EXPERIENCE_ACCEPTABLE = (3.0, 13.0)    # Wider acceptable range
EXPERIENCE_HARD_MIN = 2.0              # Below this → filter out
EXPERIENCE_HARD_MAX = 15.0             # Above this → filter out

# ---------------------------------------------------------------------------
# Location preferences (from JD)
# ---------------------------------------------------------------------------
PREFERRED_CITIES = [
    "pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram",
    "bengaluru", "bangalore", "new delhi", "navi mumbai", "thane",
]
PREFERRED_COUNTRY = "India"

# ---------------------------------------------------------------------------
# Notice period (JD: "sub-30-day preferred; can buy out up to 30 days")
# ---------------------------------------------------------------------------
IDEAL_NOTICE_DAYS = 30
MAX_COMFORTABLE_NOTICE_DAYS = 60

# ---------------------------------------------------------------------------
# Title relevance tiers
# These scores reflect how closely a title matches "Senior AI Engineer"
# ---------------------------------------------------------------------------
TITLE_RELEVANCE = {
    # Tier 1 — Direct match (0.90 - 1.00)
    "AI Engineer": 1.00,
    "Senior AI Engineer": 1.00,
    "ML Engineer": 0.95,
    "Senior Machine Learning Engineer": 0.98,
    "Machine Learning Engineer": 0.95,
    "Junior ML Engineer": 0.72,

    # Tier 2 — Strong adjacent (0.60 - 0.85)
    "Data Scientist": 0.80,
    "Data Engineer": 0.72,
    "Backend Engineer": 0.68,
    "Analytics Engineer": 0.65,
    "Software Engineer": 0.63,
    "Data Analyst": 0.58,

    # Tier 3 — Moderate (0.30 - 0.55)
    "Full Stack Developer": 0.52,
    "Cloud Engineer": 0.48,
    "DevOps Engineer": 0.42,
    "Java Developer": 0.38,
    "Frontend Engineer": 0.30,
    ".NET Developer": 0.28,
    "Mobile Developer": 0.25,
    "QA Engineer": 0.28,

    # Tier 4 — Non-tech roles (0.02 - 0.15)
    "Business Analyst": 0.12,
    "Project Manager": 0.12,
    "HR Manager": 0.03,
    "Marketing Manager": 0.03,
    "Accountant": 0.02,
    "Sales Executive": 0.02,
    "Customer Support": 0.04,
    "Operations Manager": 0.04,
    "Content Writer": 0.04,
    "Civil Engineer": 0.04,
    "Mechanical Engineer": 0.04,
    "Graphic Designer": 0.03,
}

# Non-tech titles that should generally be filtered unless career shows AI work
NON_TECH_TITLES = {
    "HR Manager", "Marketing Manager", "Accountant", "Sales Executive",
    "Operations Manager", "Content Writer", "Civil Engineer",
    "Mechanical Engineer", "Graphic Designer", "Customer Support",
}

# Titles that are borderline — keep but score low
BORDERLINE_TITLES = {
    "Business Analyst", "Project Manager",
}

# ---------------------------------------------------------------------------
# Consulting companies (JD: entire career at these = disqualifier)
# ---------------------------------------------------------------------------
CONSULTING_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mindtree", "mphasis", "ltimindtree",
    "l&t infotech", "hexaware", "persistent", "zensar", "cyient",
    "birlasoft", "sonata software", "niit technologies",
]

# ---------------------------------------------------------------------------
# Industry relevance scores
# ---------------------------------------------------------------------------
INDUSTRY_RELEVANCE = {
    "AI/ML": 1.00,
    "AI Services": 0.95,
    "Conversational AI": 0.90,
    "Voice AI": 0.88,
    "HealthTech AI": 0.88,
    "SaaS": 0.78,
    "Software": 0.72,
    "Fintech": 0.65,
    "AdTech": 0.62,
    "E-commerce": 0.60,
    "EdTech": 0.55,
    "Insurance Tech": 0.52,
    "Gaming": 0.50,
    "HealthTech": 0.50,
    "Food Delivery": 0.45,
    "Internet": 0.48,
    "Media": 0.40,
    "Consumer Electronics": 0.35,
    "Transportation": 0.30,
    "IT Services": 0.22,
    "Consulting": 0.18,
    "Manufacturing": 0.08,
    "Conglomerate": 0.08,
    "Paper Products": 0.04,
}

# ---------------------------------------------------------------------------
# Core AI/ML skill weights for scoring
# Higher weight = more relevant to this specific JD
# ---------------------------------------------------------------------------
SKILL_WEIGHTS = {
    # Must-have skills (weight 2.5 - 3.0)
    "sentence-transformers": 3.0, "FAISS": 3.0, "Pinecone": 3.0,
    "Weaviate": 3.0, "Qdrant": 3.0, "Milvus": 3.0,
    "Elasticsearch": 2.8, "OpenSearch": 2.8,
    "Chroma": 2.5, "ChromaDB": 2.5,

    # Core ML/AI (weight 2.0 - 2.5)
    "NLP": 2.5, "PyTorch": 2.5, "TensorFlow": 2.3,
    "Hugging Face": 2.5, "Transformers": 2.5,
    "Deep Learning": 2.4, "Machine Learning": 2.3,
    "RAG": 2.5, "Information Retrieval": 2.8,
    "Recommendation Systems": 2.5, "Search": 2.3,
    "Ranking": 2.8,

    # Nice-to-have (weight 1.5 - 2.0)
    "LoRA": 2.0, "Fine-tuning LLMs": 2.0, "XGBoost": 1.8,
    "LightGBM": 1.8, "Feature Engineering": 1.8,
    "Statistical Modeling": 1.5, "MLflow": 1.8,
    "Weights & Biases": 1.7, "BentoML": 1.5,

    # Good technical foundation (weight 1.0 - 1.5)
    "Python": 1.8, "Spark": 1.5, "PySpark": 1.5,
    "Airflow": 1.2, "SQL": 1.2, "Pandas": 1.3,
    "NumPy": 1.3, "scikit-learn": 1.5, "Keras": 1.5,
    "ONNX": 1.5, "TensorRT": 1.5, "Triton": 1.5,
    "Docker": 1.2, "Kubernetes": 1.2,
    "AWS": 1.0, "GCP": 1.0, "Azure": 1.0,
    "Databricks": 1.2, "Snowflake": 0.8,
    "BigQuery": 0.8, "dbt": 0.8,
    "Apache Beam": 0.8, "Apache Flink": 0.8,
    "Kafka": 1.0,

    # Lower-relevance tech (weight 0.2 - 0.5)
    "Java": 0.5, "Go": 0.5, "Rust": 0.5,
    "C++": 0.5, "Scala": 0.6,
    "Node.js": 0.3, "Express": 0.2,
    "React": 0.2, "Angular": 0.2, "Vue.js": 0.2,
    "JavaScript": 0.3, "TypeScript": 0.3,
    "HTML": 0.1, "CSS": 0.1, "Tailwind": 0.1,
    "Redux": 0.1, "Next.js": 0.2, "Webpack": 0.1,
    "GraphQL": 0.3, "REST APIs": 0.4,
    "Flask": 0.5, "FastAPI": 0.6, "Django": 0.4,
    "Spring Boot": 0.3, "MongoDB": 0.4,
    "PostgreSQL": 0.5, "Redis": 0.4, "MySQL": 0.3,
    "CI/CD": 0.5, "Terraform": 0.4, "Git": 0.3,

    # Non-tech / irrelevant (weight 0.0 - 0.1)
    "LangChain": 1.2,  # JD warns about LangChain-only, but still ML-adjacent
    "Sales": 0.0, "Accounting": 0.0, "Tally": 0.0,
    "Excel": 0.1, "PowerPoint": 0.0, "Photoshop": 0.0,
    "Illustrator": 0.0, "Figma": 0.1,
    "SEO": 0.0, "Content Writing": 0.0, "Marketing": 0.0,
    "Salesforce CRM": 0.0, "SAP": 0.0, "Six Sigma": 0.0,
    "Scrum": 0.1, "Agile": 0.1, "Project Management": 0.1,
    "ETL": 0.6,

    # Specific ML sub-domains
    "Image Classification": 0.8, "Object Detection": 0.7,
    "Computer Vision": 0.7, "Speech Recognition": 0.5,
    "TTS": 0.4, "GANs": 0.8, "Reinforcement Learning": 0.8,

    # Not in the data but common
    "OpenCV": 0.6, "NLTK": 1.0, "spaCy": 1.2,
    "Gensim": 1.2, "Word2Vec": 1.2, "BERT": 2.0,
    "GPT": 1.5, "T5": 1.5, "LLM": 2.0,
}

# ---------------------------------------------------------------------------
# Career description keywords for trajectory scoring
# ---------------------------------------------------------------------------
HIGH_SIGNAL_CAREER_KEYWORDS = [
    "ranking system", "ranking model", "ranked", "reranking", "re-ranking",
    "recommendation system", "recommendation engine", "recommender",
    "search system", "search engine", "search quality", "search relevance",
    "retrieval system", "retrieval pipeline", "information retrieval",
    "embeddings", "embedding model", "vector", "vector search",
    "semantic search", "dense retrieval", "hybrid retrieval",
    "machine learning model", "ml model", "ml pipeline", "ml system",
    "deployed model", "model deployment", "model serving",
    "production ml", "production machine learning",
    "a/b test", "ab test", "a/b testing",
    "evaluation framework", "offline evaluation", "online evaluation",
    "ndcg", "precision", "recall", "mrr",
    "feature engineering", "feature store", "feature pipeline",
    "model training", "training pipeline", "training data",
    "fine-tun", "fine tun", "finetun",
    "inference", "inference pipeline", "batch inference", "real-time inference",
    "candidate matching", "talent matching", "job matching",
    "nlp", "natural language processing", "text classification",
    "named entity", "sentiment analysis", "text mining",
    "information extraction", "knowledge graph",
]

MEDIUM_SIGNAL_CAREER_KEYWORDS = [
    "python", "data science", "data scientist",
    "analytics", "data analytics", "data analysis",
    "deep learning", "neural network", "transformer",
    "bert", "gpt", "llm", "large language model",
    "computer vision", "image recognition",
    "api", "rest api", "graphql", "microservice",
    "backend", "backend system", "server-side",
    "distributed", "scalable", "high-performance",
    "spark", "kafka", "airflow", "pipeline",
    "data pipeline", "etl", "data warehouse",
    "cloud", "aws", "gcp", "azure",
    "docker", "kubernetes", "containeriz",
    "tensorflow", "pytorch", "scikit",
    "xgboost", "gradient boosting",
    "sql", "database", "postgresql",
    "open-source", "open source",
]

NEGATIVE_CAREER_KEYWORDS = [
    "customer support", "support agent", "support team",
    "sales target", "sales pipeline", "cold call",
    "marketing campaign", "brand awareness", "social media marketing",
    "accounting", "financial reporting", "tax filing", "audit",
    "hr process", "recruitment process", "onboarding",
    "content writing", "seo strategy", "editorial calendar",
    "mechanical engineering", "mechanical design",
    "civil engineering", "structural",
    "cad", "solidworks", "creo", "ansys",
    "brand design", "packaging design", "brand identity",
    "operations management", "warehouse", "fulfillment",
    "logistics", "supply chain",
]

# ---------------------------------------------------------------------------
# Education field relevance
# ---------------------------------------------------------------------------
EDUCATION_FIELD_HIGH = [
    "machine learning", "artificial intelligence", "data science",
    "natural language processing", "deep learning",
]
EDUCATION_FIELD_MEDIUM = [
    "computer science", "computer engineering", "software engineering",
    "information technology", "computational",
]
EDUCATION_FIELD_LOW = [
    "electronics", "electrical", "mathematics", "statistics",
    "physics", "applied mathematics",
]

# ---------------------------------------------------------------------------
# Relevant certifications
# ---------------------------------------------------------------------------
CERTIFICATION_RELEVANCE = {
    "aws certified machine learning": 1.0,
    "google cloud professional ml engineer": 1.0,
    "google cloud professional data engineer": 0.8,
    "tensorflow developer certificate": 0.9,
    "azure data scientist associate": 0.8,
    "azure ai engineer associate": 0.9,
    "aws certified solutions architect": 0.5,
    "aws certified cloud practitioner": 0.3,
    "databricks certified": 0.6,
    "deeplearning.ai": 0.7,
    "coursera deep learning": 0.4,
    "scrum master": 0.05,
    "pmp": 0.05,
    "six sigma": 0.0,
}
