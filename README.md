# CodeArena

Full-stack programming contest platform with:

- Django + DRF backend
- React + Vite frontend
- PostgreSQL database
- Docker local environment
- Render + Vercel + Neon deployment setup

## Local Development

```bash
docker compose up --build
```

The local stack includes Django, frontend, PostgreSQL, Redis, Celery, and Nginx.

## Demo Data

After migrations, create demo admin, problems, contests, participants, and submissions:

```bash
docker compose exec django python manage.py seed_demo --admin-password 'change-this-password'
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the Render backend, Vercel frontend, and Neon database setup.
