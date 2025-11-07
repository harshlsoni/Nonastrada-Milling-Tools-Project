# Dockerfile for the Flask demo app (No Kafka)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# copy requirements and install system deps
COPY requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
# install base requirements (may include large packages such as torch)
RUN pip --no-cache-dir install -r /app/requirements.txt
# install extras required by the pipeline/demo (removed kafka-python)
RUN pip --no-cache-dir install Flask PyWavelets

# copy code and files
COPY Code/ /app/Code/
COPY Files/ /app/Files/

# create uploads directory
RUN mkdir -p /app/uploads

WORKDIR /app

ENV FLASK_ENV=production
ENV UPLOAD_FOLDER=/app/uploads
EXPOSE 5000

# Start Flask app directly (no Kafka wait)
CMD ["python", "/app/Code/flask_app.py"]
