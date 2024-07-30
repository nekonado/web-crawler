FROM python:3.9-slim

WORKDIR /app

# Log output immediately to stdout without buffering
ENV PYTHONUNBUFFERED=1

COPY requirements.txt crawler.py config.json ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "crawler.py"]
