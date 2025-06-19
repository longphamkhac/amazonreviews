FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY insert_reviews.py .
COPY postgresql_client.py .
COPY data/processed/Magazine_Subscriptions.jsonl ./data/processed/Magazine_Subscriptions.jsonl

CMD ["sh", "-c", "python insert_reviews.py"]