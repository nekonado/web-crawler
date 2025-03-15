FROM python:3.9-slim

WORKDIR /app

# Log output immediately to stdout without buffering
ENV PYTHONUNBUFFERED=1

# Copy requirements and Python files first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY crawler.py config.json ./
COPY crawler/ ./crawler/

CMD ["python", "crawler.py"]
