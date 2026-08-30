FROM python:3.11-slim

WORKDIR /app

# Instalacja zależności systemowych dla Docling i PyMuPDF
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-pol \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 7860

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
