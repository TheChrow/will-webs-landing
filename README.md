# Will-Webs — Sitio web

Monorepo del sitio de Will-Webs: frontend, API FastAPI, MySQL y proxy, todo en Docker.
Especificación completa en [`specs/001-will-webs-site/`](specs/001-will-webs-site/spec.md).

**Estado: Fase 0 (cimientos)** — stack dockerizado, API con health checks, MySQL con usuarios
de mínimo privilegio y Alembic listo. El frontend aún sirve la landing estática (`frontend/legacy/`)
hasta la migración a React (Fase 2).

## Levantar en desarrollo

Requisitos: Docker Desktop (Compose v2).

```powershell
copy .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

| URL | Qué es |
|---|---|
| http://localhost:8088 | Sitio (vía proxy Caddy) |
| http://localhost:8088/api/v1/health | Liveness de la API |
| http://localhost:8088/api/v1/health/ready | Readiness (incluye ping a MySQL) |
| http://localhost:8000/api/docs | Swagger (solo dev) |
| http://localhost:8025 | Mailpit (correo de prueba) |
| `localhost:3307` | MySQL (solo desde 127.0.0.1) |

Los puertos locales se cambian en `.env` (`HTTP_PORT`, `DB_PORT_LOCAL`).

### Comandos útiles

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pytest
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend ruff check .
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm migrate alembic revision --autogenerate -m "mensaje"
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

`down -v` borra también el volumen de MySQL (los scripts de `db/init/` vuelven a ejecutarse en el próximo arranque).

## Producción

1. Crear los secretos (archivos de una línea, ignorados por git): `secrets/mysql_root_password`,
   `secrets/migrator_db_password`, `secrets/app_db_password`.
2. En `.env`: `APP_ENV=production`, `SITE_ADDRESS=<tu-dominio>` (Caddy obtiene TLS automáticamente)
   y `ALLOWED_HOSTS=<tu-dominio>,localhost,127.0.0.1`.
3. Levantar:

```powershell
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

En prod solo el proxy expone puertos (80/443), MySQL queda en una red interna sin salida a Internet,
se activa HSTS y Swagger se desactiva.

## Estructura

```
backend/            FastAPI + SQLAlchemy 2 (async) + Alembic · dependencias con uv (uv.lock)
  app/core/         configuración por entorno (soporta Docker secrets)
  app/db/           engine, sesiones, Base con naming convention
  app/api/v1/       routers (health)
  migrations/       Alembic (usa el usuario migrator)
frontend/           Nginx sin privilegios sirviendo frontend/legacy (landing Bootstrap 5)
db/init/            crea el usuario de aplicación con privilegios solo DML
proxy/Caddyfile     TLS, cabeceras de seguridad, límite de body, ruteo / y /api
specs/              especificaciones
```

### Usuarios de base de datos

| Usuario | Privilegios | Lo usa |
|---|---|---|
| `willwebs_migrator` | ALL sobre `willwebs` | Solo el job `migrate` (Alembic) |
| `willwebs_app` | SELECT, INSERT, UPDATE, DELETE | La API en ejecución |

## Paleta de marca

| Color | Hex | Uso |
|---|---|---|
| Azul marino oscuro | `#09274F` | Fondos oscuros (navbar, hero, footer) |
| Azul medio | `#094183` | Títulos y acentos |
| Azul vivo | `#014DBF` | Primario / CTA |

Definidos en `frontend/legacy/styles.css` (`:root`).
