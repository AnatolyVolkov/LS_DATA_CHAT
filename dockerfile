# Dockerfile
FROM python:3.11-slim

# Создаем непривилегированного пользователя (безопасность)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Устанавливаем системные зависимости (curl для healthcheck, ssh-клиент для туннеля)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Оптимизация Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для .streamlit и копируем конфиг (если есть)
RUN mkdir -p /app/.streamlit
# Если у вас есть продакшн-конфиг, раскомментируйте:
# COPY .streamlit/config.prod.toml /app/.streamlit/config.toml

# Меняем владельца файлов на appuser
RUN chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Открываем порт
EXPOSE 8501

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Запускаем приложение
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]