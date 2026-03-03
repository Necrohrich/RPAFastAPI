FROM python:3.12-slim
LABEL authors="Elshan"

WORKDIR /app

# системные зависимости (если нужны)
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1