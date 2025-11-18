# Multi-stage build для оптимизации памяти
# Stage 1: Установка зависимостей
FROM python:3.11-slim as builder

WORKDIR /install

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости в отдельную директорию
RUN pip install --prefix=/install --no-cache-dir --no-warn-script-location -r requirements.txt

# Stage 2: Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для OpenCV и других библиотек
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные зависимости из builder stage
COPY --from=builder /install /usr/local

# Копируем исходный код приложения
COPY src/ ./src/

# Копируем модель
COPY models/ ./models/

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Запускаем приложение
CMD ["python", "-m", "src.main"]