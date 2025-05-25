# Используем базовый образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Сборка статических файлов, миграции и запуск приложения
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn app.wsgi:application --bind 0.0.0.0:8000"]