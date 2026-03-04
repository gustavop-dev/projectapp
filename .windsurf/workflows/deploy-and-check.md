---
description: Deploy latest master to production server for projectapp
---

# Deploy projectapp to Production

Run these steps on the production server at `/home/ryzepeck/webapps/projectapp` to deploy the latest `main` branch.

## Pre-Deploy

// turbo
1. Quick status snapshot before deploy:
```bash
bash ~/scripts/quick-status.sh
```

## Deploy Steps

// turbo
2. Pull the latest code from main:
```bash
cd /home/ryzepeck/webapps/projectapp && git pull origin main
```

3. Install backend dependencies and run migrations:
```bash
cd /home/ryzepeck/webapps/projectapp/backend && source venv/bin/activate && pip install -r requirements.txt && DJANGO_SETTINGS_MODULE=projectapp.settings_prod python manage.py migrate
```

4. Build the frontend (Nuxt generate + copy to Django static):
```bash
cd /home/ryzepeck/webapps/projectapp/frontend && npm ci && npm run build:django
```

5. Collect static files:
```bash
cd /home/ryzepeck/webapps/projectapp/backend && source venv/bin/activate && DJANGO_SETTINGS_MODULE=projectapp.settings_prod python manage.py collectstatic --noinput
```

6. Restart services:
```bash
sudo systemctl restart projectapp && sudo systemctl restart projectapp-huey
```

## Post-Deploy Verification

// turbo
7. Run post-deploy check for projectapp:
```bash
bash ~/scripts/post-deploy-check.sh projectapp
```
Expected: PASS on all checks, FAIL=0.

8. If something fails, check the logs:
```bash
sudo journalctl -u projectapp.service --no-pager -n 30
sudo journalctl -u projectapp-huey.service --no-pager -n 30
sudo tail -20 /var/log/nginx/error.log
```

## Architecture Reference

- **Domain**: `projectapp.co` / `www.projectapp.co`
- **Backend**: Django (`projectapp` module), settings selected via `DJANGO_SETTINGS_MODULE=projectapp.settings_prod` in systemd unit
- **Frontend**: Nuxt 3 SSG → `backend/static/frontend/` + Django `serve_nuxt` catch-all view
- **Services**: `projectapp.service` (Gunicorn via socket), `projectapp.socket`, `projectapp-huey.service`
- **Nginx**: `/etc/nginx/sites-available/projectapp`
- **Socket**: `/run/projectapp.sock`
- **Static**: `/home/ryzepeck/webapps/projectapp/backend/staticfiles/`
- **Media**: `/home/ryzepeck/webapps/projectapp/backend/media/`
- **Resource limits**: MemoryMax=350M, CPUQuota=40%, OOMScoreAdjust=300

## Notes

- `~/scripts` is a symlink to `/home/ryzepeck/webapps/ops/vps/`.
- Frontend uses `npm run build:django` which runs `nuxi generate` with `NUXT_APP_CDN_URL=/static/frontend/` and copies output to `backend/static/frontend/`.
- `DJANGO_SETTINGS_MODULE=projectapp.settings_prod` must be set for migrate and collectstatic commands (manage.py defaults to settings_dev).
