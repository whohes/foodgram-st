**Foodgram** — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.


## Стек технологий

* Python 3.13
* Django 5.2
* Django REST Framework
* PostgreSQL
* Docker
* Docker Compose
* Nginx
* Gunicorn
* GitHub Actions

## Запуск с Docker

### 1. Клонирование репозитория

```bash
git clone https://github.com/whohes/foodgram-st.git
cd foodgram-st
```

### 2. Создание и настройка `.env` файла

В корне проекта создайте файл `.env` со следующим содержимым:

```env
DEBUG=True
SECRET_KEY=django-insecure-123
ALLOWED_HOSTS=127.0.0.1,localhost,backend
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram
DB_HOST=db
DB_PORT=5432
```

### 3. Сборка и запуск контейнеров

Перейдите в директорию `infra/` и выполните:

```bash
docker-compose up -d --build
```

### 4. Применение миграций и сбор статики

```bash

docker-compose exec backend python manage.py migrate users

docker-compose exec backend python manage.py migrate recipes

docker-compose exec backend python manage.py migrate 

docker compose exec backend python manage.py load_ingredients

docker-compose exec backend python manage.py collectstatic --noinput
```

### 5. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```
### 5.1 Создание пользователей и добавление их рецептов

```bash
docker-compose exec backend python manage.py load_users

docker-compose exec backend python manage.py load_recipes
```

### 7. Доступ к приложению

* Фронтенд: [http://localhost/](http://localhost/)
* Админ-зона: [http://localhost/admin/](http://localhost/admin/)
* API: [http://localhost/api/](http://localhost/api/)

## Автор

**Денцель Артур**

## Ссылка на GitHub

https://github.com/whohes
