# Установка зависимостей
FROM python:3.11-slim as builder

WORKDIR /install

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости в отдельную директорию
RUN pip install --verbose --prefix=/install --no-cache-dir --no-warn-script-location -r requirements.txt

# Финальный образ
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY src/ ./src/

COPY models/ ./models/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Запускаем приложение
CMD ["python", "-m", "src.main"]