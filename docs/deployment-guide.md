# Deployment Guide — projectapp

Step-by-step guide to deploy projectapp from `main` to production.

---

## Prerequisites

- Ubuntu/Debian with Python 3.12+, Node 22+, MySQL 8+, Redis, Nginx
- SSL certificate (Let's Encrypt via Certbot)
- Domain `projectapp.co` pointing to the server

---

## Initial Deployment (first time)

### 1. Clone the repository

```bash
git clone https://github.com/carlos18bp/projectapp.git /home/ryzepeck/webapps/projectapp
cd /home/ryzepeck/webapps/projectapp
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Backend .env

```bash
cp .env.example .env
nano .env   # Fill ALL variables — see "Production .env values" below
```

### 4. Database migrations

```bash
source venv/bin/activate
DJANGO_SETTINGS_MODULE=projectapp.settings_prod python manage.py migrate
```

### 5. Frontend setup + build

```bash
cd ../frontend
npm ci
npm run build:django
```

This generates:
- `backend/static/frontend/` — Nuxt pre-rendered pages and assets

### 6. Collect static files

```bash
cd ../backend
source venv/bin/activate
DJANGO_SETTINGS_MODULE=projectapp.settings_prod python manage.py collectstatic --noinput
```

### 7. Install systemd services

```bash
sudo cp scripts/systemd/projectapp.service /etc/systemd/system/projectapp.service
sudo cp scripts/systemd/projectapp.socket /etc/systemd/system/projectapp.socket
sudo cp scripts/systemd/huey.service /etc/systemd/system/projectapp-huey.service
sudo systemctl daemon-reload
sudo systemctl enable --now projectapp.socket
sudo systemctl enable --now projectapp.service
sudo systemctl enable --now projectapp-huey
```

### 8. Configure Nginx

```bash
sudo cp scripts/nginx/projectapp.conf /etc/nginx/sites-available/projectapp
sudo ln -s /etc/nginx/sites-available/projectapp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 9. Verify

```bash
curl -I https://www.projectapp.co
sudo systemctl status projectapp
sudo systemctl status projectapp-huey
```

---

## Updates (future deploys)

```bash
cd /home/ryzepeck/webapps/projectapp
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=projectapp.settings_prod python manage.py migrate

# Frontend
cd ../frontend
npm ci
npm run build:django

# Collect static + restart
cd ../backend
source venv/bin/activate
DJANGO_SETTINGS_MODULE=projectapp.settings_prod python manage.py collectstatic --noinput
sudo systemctl restart projectapp
sudo systemctl restart projectapp-huey
```

---

## Production .env values

### Backend (`backend/.env`)

```env
DJANGO_ENV=production
DJANGO_SECRET_KEY=<generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=projectapp.co,www.projectapp.co
DJANGO_LOG_LEVEL=WARNING

# Database (MySQL)
DB_NAME=projectapp_db
DB_USER=<db-user>
DB_PASSWORD=<db-password>
DB_HOST=localhost
DB_PORT=3306

# Email (GoDaddy SMTP)
EMAIL_HOST=smtpout.secureserver.net
EMAIL_PORT=465
EMAIL_USE_SSL=true
EMAIL_HOST_USER=team@projectapp.co
EMAIL_HOST_PASSWORD=<email-password>
DEFAULT_FROM_EMAIL=team@projectapp.co
NOTIFICATION_EMAIL=dev.gustavo.perezp@gmail.com

# WhatsApp (CallMeBot)
WHATSAPP_PHONE=<phone-with-country-code>
CALLMEBOT_API_KEY=<api-key>

# CORS / CSRF
DJANGO_CORS_ALLOWED_ORIGINS=https://projectapp.co,https://www.projectapp.co
DJANGO_CSRF_TRUSTED_ORIGINS=https://projectapp.co,https://www.projectapp.co

# Redis / Huey
REDIS_URL=redis://localhost:6379/5

# Backups
BACKUP_STORAGE_PATH=/var/backups/projectapp

# Monitoring
ENABLE_SILK=false
SLOW_QUERY_THRESHOLD_MS=500
N_PLUS_ONE_THRESHOLD=10
```

---

## Credential Rotation (IMPORTANT)

The following credentials were exposed in the git history of the `production-projectapp` branch and **should be rotated**:

- **MySQL password** (hardcoded in old settings.py)
- **Email password** (hardcoded in old settings.py)
- **Django SECRET_KEY** (the insecure default from the old production branch)
- **CallMeBot API Key** (hardcoded in old settings.py)

---

## Architecture Overview

```
Client (HTTPS)
    │
    ▼
Nginx (SSL termination)
    ├── /static/  → backend/staticfiles/
    ├── /media/   → backend/media/
    └── /*        → unix:/run/projectapp.sock
                        │
                        ▼
                   Gunicorn (2 workers)
                        │
                        ▼
                   Django (settings_prod)
                   ├── /api/*     → DRF views
                   ├── /admin/*   → Django admin
                   └── /*         → serve_nuxt (pre-rendered Nuxt pages)
```

Key settings in production:
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` — prevents redirect loop
- `SECURE_SSL_REDIRECT = True` — forces HTTPS
- `STATIC_ROOT = BASE_DIR / 'staticfiles'` — collectstatic destination
- `STATICFILES_DIRS = [BASE_DIR / 'static']` — Nuxt build output location
