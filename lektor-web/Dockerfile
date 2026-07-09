FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg mkvtoolnix \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask

# Kopiujemy lektor.py do katalogu roboczego /app
COPY lektor.py /app/lektor.py
COPY app.py /app/app.py
COPY templates/ /app/templates/

EXPOSE 5000
CMD ["python3", "app.py"]
