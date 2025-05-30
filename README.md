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
docker exec foodgram_back python manage.py makemigrations users

docker exec foodgram_back python manage.py makemigrations recipes

<<<<<<< HEAD
=======
docker compose exec backend python manage.py load_ingredients

>>>>>>> 81a8c6bcf67b8542fee438b13229c51fcddd37ed
docker-compose exec backend python manage.py migrate

docker-compose exec backend python manage.py collectstatic --noinput
```

### 5. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```


### 7. Доступ к приложению

* Фронтенд: [http://localhost/](http://localhost/)
* Админ-зона: [http://localhost/admin/](http://localhost/admin/)
* API: [http://localhost/api/](http://localhost/api/)

## Автор

**Денцель Артур**

## Ссылка на GitHub

https://github.com/whohes
