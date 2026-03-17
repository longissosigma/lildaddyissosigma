FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OPENROUTER_API_KEY=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

CMD gunicorn dadweb:app