FROM python:3.11-slim

WORKDIR /app

# Copy source
COPY src/ src/
COPY rank.py .
COPY requirements.txt .

# No dependencies needed for the ranking pipeline
# Only install streamlit if you want the demo
# RUN pip install --no-cache-dir -r requirements.txt

# Default: run ranking pipeline
ENTRYPOINT ["python", "rank.py"]
CMD ["--candidates", "/data/candidates.jsonl", "--out", "/output/submission.csv"]
