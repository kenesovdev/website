# Deployment: Render + Vercel + Neon

This repository is prepared for:

- Backend: Render Docker Web Service
- Frontend: Vercel Vite project
- Database: Neon Postgres

## 1. Neon

Create a Neon project and copy the Postgres connection string. Use the SSL form, for example:

```text
postgresql://USER:PASSWORD@HOST.neon.tech/DB?sslmode=require
```

## 2. Render Backend

Create the backend from `render.yaml` or create it manually:

- Service type: Web Service
- Runtime: Docker
- Root directory: `backend`
- Health check path: `/health/`

Required environment variables:

```text
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
DATABASE_URL=<Neon connection string>
ALLOWED_HOSTS=<your-render-host>.onrender.com
CORS_ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app
CSRF_TRUSTED_ORIGINS=https://<your-vercel-app>.vercel.app,https://<your-render-host>.onrender.com
REFRESH_COOKIE_SECURE=True
REFRESH_COOKIE_SAMESITE=None
SECRET_KEY=<long random value>
JWT_ACCESS_SECRET=<long random value>
JWT_REFRESH_SECRET=<long random value>
```

Optional:

```text
REDIS_URL=<Render Key Value / Redis URL>
CELERY_TASK_ALWAYS_EAGER=False
```

If `REDIS_URL` is not set, cache and channel layers fall back to in-memory mode and Celery tasks run eagerly in the web process. That is enough for a demo, but a real public judge should use Redis plus a separate worker.

After the first successful deploy, seed demo data from the Render Shell:

```bash
python manage.py seed_demo --admin-password 'change-this-password'
```

## 3. Vercel Frontend

Create a Vercel project with:

- Root directory: `frontend`
- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist`

Environment variables:

```text
VITE_API_URL=https://<your-render-host>.onrender.com
```

`VITE_WS_URL` is optional. If it is omitted, the frontend derives it from `VITE_API_URL`.

## 4. Production Notes

- The browser refresh token is a cross-site cookie when Vercel and Render use different domains, so production needs `REFRESH_COOKIE_SAMESITE=None` and `REFRESH_COOKIE_SECURE=True`.
- Add every frontend domain to `CORS_ALLOWED_ORIGINS`; Vercel preview URLs need to be added separately.
- This app executes submitted code. Do not open judging to unknown users without stronger sandboxing, quotas, and isolation.
