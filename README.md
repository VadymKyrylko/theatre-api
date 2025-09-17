# 🎭 Theatre API

A Django REST Framework–based API for a theatre booking system.  
The project runs inside Docker containers with PostgreSQL as the database.

## Features
- Django 5 + Django REST Framework
- PostgreSQL 16
- Dockerized environment (web + db services)
- Custom user model
- JWT authentication (via `djangorestframework-simplejwt`)
- Static & media file handling with Docker volumes
- Custom management command `wait_for_db` to ensure database readiness

## Project Structure
|---theatre/             # Theatre app
|---user/                # Custom user app
|---config/              # Django settings & configuration
|---management/commands/ # Custom commands (e.g., wait_for_db)
|---Dockerfile
|---docker-compose.yml
|---requirements.txt
|---.env.example

## Setup and installation

### 1. Clone the repository

    git clone https://github.com/your-username/theatre-api.git
    cd theatre-api

### 2. Create .env file and write your values

    SECRET_KEY=your_secret_key_here
    DEBUG=True
    ALLOWED_HOSTS=127.0.0.1,localhost
    POSTGRES_DB=theatre_db
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=your_password_here
    POSTGRES_HOST=db
    POSTGRES_PORT=5432

### 3. Build and start containers
    
    docker-compose build
    docker-compose up -d

### 4. Run migrations

    docker-compose exec web python manage.py migrate

### 5. Create superuser

    docker-compose exec web python manage.py createsuperuser

### 6. Collect static files
    docker-compose exec web python manage.py collectstatic --noinput

_______________________________________
## Access
API ROOT: http://127.0.0.1:8001/
Admin panel: http://127.0.0.1:8001/admin/

## Note
    The wait_for_db management command ensures the app waits until PostgreSQL is ready before applying migrations.
