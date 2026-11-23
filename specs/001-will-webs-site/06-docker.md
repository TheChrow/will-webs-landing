# 06 — Dockerización desde el inicio

## Objetivo
Que todo el stack (frontend, backend, MySQL, proxy) corra en contenedores desde el primer commit, con paridad dev/prod.

## Servicios

| Servicio | Imagen base | Dev | Prod |
|---|---|---|---|
| `frontend` | `node:22-alpine` (build) → `nginx:1.27-alpine` (runtime) | Vite dev server con HMR, bind mount de `src/` | Build estático servido por Nginx, sin Node en runtime |
| `backend` | `python:3.12-slim` multi-stage | `uvicorn --reload`, bind mount | `gunicorn -k uvicorn.workers.UvicornWorker`, imagen inmutable |
| `db` | `mysql:8.4` (LTS) | Puerto 3306 expuesto solo a `127.0.0.1` | **Sin puerto publicado**, volumen persistente |
| `proxy` | `caddy:2-alpine` | Opcional | TLS automático, headers de seguridad, rate limit |
| `mailpit` | `axllent/mailpit` | SMTP falso para probar correos | — |

## Requisitos
- **Multi-stage builds**; imágenes finales mínimas (`slim`/`alpine`/distroless) y con versiones fijadas (nada de `latest`).
- **Usuario no-root** (`USER app`) en backend y frontend; `read_only: true` + `tmpfs` donde sea posible.
- `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`.
- **Healthchecks** en los 4 servicios; `depends_on: condition: service_healthy` (backend espera a MySQL).
- **Redes**: `public` (proxy↔frontend/backend) e `internal` (backend↔db, `internal: true`).
- **Secretos**: `.env` fuera de git; `.env.example` versionado; en prod usar Docker secrets (`/run/secrets/*`) para contraseñas de DB y claves.
- **Migraciones** Alembic se ejecutan como paso explícito (`docker compose run --rm backend alembic upgrade head`) o servicio `migrate` one-shot, no en cada arranque de worker.
- `.dockerignore` en cada servicio (excluir `.git`, `node_modules`, `.env`, `__pycache__`).
- Límites de recursos (`mem_limit`, `cpus`) en prod.
- Backups: job `mysqldump` programado (cron en host o contenedor) a almacenamiento externo, con prueba de restauración documentada.

## Comandos objetivo

```powershell
copy .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## CI (GitHub Actions)
- Build de imágenes en cada PR.
- Lint + tests (backend `pytest`, frontend `vitest`).
- Escaneo de imágenes con **Trivy** y de Dockerfiles con **hadolint**; falla con *high/critical*.

## Entregables
- `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml`
- `frontend/Dockerfile`, `backend/Dockerfile`, `proxy/Caddyfile`
- `.env.example`, `.dockerignore`s
- Sección "Cómo levantar" en el README raíz

## Criterios de aceptación
- [ ] Clonar + copiar `.env` + un comando → sitio en `http://localhost` y API en `/api/v1/health`.
- [ ] MySQL no accesible desde fuera de la red interna en prod.
- [ ] Ningún contenedor corre como root.
- [ ] Trivy sin vulnerabilidades high/critical.
