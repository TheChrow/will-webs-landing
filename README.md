# Will-Webs — Sitio web

Monorepo del sitio de Will-Webs: frontend, API FastAPI, MySQL y proxy, todo en Docker.
Especificación completa en [`specs/001-will-webs-site/`](specs/001-will-webs-site/spec.md).

**Estado: Fase 2 (frontend React)** — sitio en React Router v8 pre-renderizado a HTML estático,
consumiendo la API: servicios, contenido, formulario de contacto protegido y páginas legales.
Datos en [Master Data](docs/master-data.md); decisiones de UX en la [auditoría UX/UI](docs/ux-audit.md).

## Frontend

React 19 + TypeScript + React Router v8 (modo framework, `ssr: false` + `prerender`) + Vite,
Bootstrap 5.3 SCSS self-hosted, TanStack Query, React Hook Form + Zod, íconos Lucide.

- **Pre-render**: cada ruta (`/`, `/privacidad`, `/cookies`, `/terminos`, `/accesibilidad`) se genera
  como HTML en el build con el contenido de respaldo (`app/lib/fallback.ts`, igual a los seeds); al
  cargar, el navegador consulta la API y muestra los datos vigentes.
- **Producción**: Nginx sin privilegios sirve solo estáticos (sin Node). Rutas desconocidas → 404 real.
- **CSP sin `'unsafe-inline'`**: `scripts/csp.mjs` calcula en el build los hashes SHA-256 de los
  scripts inline de React Router y Nginx los emite en la cabecera. No usar `style="..."` en JSX.
- **Desarrollo**: Vite con HMR detrás del proxy (http://localhost:8088).

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm test
```

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm run typecheck
```

## API v1

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/health` · `/health/ready` | liveness / readiness (ping a MySQL) |
| GET | `/api/v1/services` · `/services/{slug}` | servicios publicados |
| GET | `/api/v1/banners` | banners publicados y vigentes |
| GET | `/api/v1/clients` | empresas publicadas **con autorización de logo** |
| GET | `/api/v1/content?prefix=hero.` · `/content/{key}` | bloques de texto publicados |
| GET | `/api/v1/legal/{privacy,cookies,terms,accessibility}` | versión vigente del documento legal |
| GET | `/api/v1/settings` | ajustes públicos del sitio |
| POST | `/api/v1/contact` | lead + consentimiento + correo de aviso (202) |

Las respuestas GET son cacheables 5 min; los errores siguen RFC 9457 (`application/problem+json`).

**`POST /contact`** valida estrictamente (sin campos extra, sin saltos de línea en cabeceras, longitudes),
exige `privacy_accepted: true` y registra el consentimiento contra la versión vigente de la
Política de Privacidad. Anti-abuso: honeypot `website`, tiempo mínimo de llenado (`elapsed_ms`),
Cloudflare Turnstile (`captcha_token`, obligatorio en prod) y rate limit de 5 envíos/hora por IP y
por email. La IP y el email del consentimiento se guardan seudonimizados (HMAC-SHA256 + pepper).

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
| http://localhost:8001/api/docs | Swagger (solo dev) |
| http://localhost:8025 | Mailpit (correo de prueba) |
| `localhost:3307` | MySQL (solo desde 127.0.0.1) |

Los puertos locales se cambian en `.env` (`HTTP_PORT`, `API_PORT_LOCAL`, `DB_PORT_LOCAL`).

### Comandos útiles

Tests (unitarios + integración contra MySQL real en la base `willwebs_test`; corren en el contenedor
`migrate`, que tiene las credenciales con permisos DDL):

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm migrate pytest
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
   `secrets/migrator_db_password`, `secrets/app_db_password`, `secrets/hash_pepper`,
   `secrets/turnstile_secret_key`, `secrets/smtp_password`. La API no arranca en producción sin
   `hash_pepper` ni `turnstile_secret_key`.
2. En `.env`: `APP_ENV=production`, `SITE_ADDRESS=<tu-dominio>` (Caddy obtiene TLS automáticamente),
   `ALLOWED_HOSTS=<tu-dominio>,localhost,127.0.0.1`, `VITE_SITE_URL=https://<tu-dominio>` y
   `VITE_TURNSTILE_SITE_KEY=<clave de sitio pública>` (se incrustan en el build del frontend).
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
  app/models/       modelos SQLAlchemy (ver docs/master-data.md)
  app/schemas/      Pydantic de entrada/salida
  app/repositories/ consultas
  app/services/     lógica: leads, captcha, correo
  app/api/v1/       routers (health, public/content, public/contact)
  app/seeds.py      master data inicial, idempotente (lo corre el job migrate)
  migrations/       Alembic (usa el usuario migrator)
docs/master-data.md diccionario de datos, ER, reglas, retención
frontend/           React Router v8 + Vite (dev) · Nginx sin privilegios (prod)
  app/routes/       páginas: home y legales (+ 404)
  app/components/   secciones del sitio y formulario de contacto
  app/lib/          cliente API, queries, esquema Zod, contenido de respaldo, SEO
  app/styles/       Bootstrap SCSS + marca
  scripts/csp.mjs   genera la CSP con hashes en el build
docs/ux-audit.md    hallazgos UX/UI y cómo se resolvieron
db/init/            crea el usuario de aplicación con privilegios solo DML
proxy/Caddyfile     TLS, cabeceras de seguridad, límite de body, ruteo / y /api
specs/              especificaciones
```

### Usuarios de base de datos

| Usuario | Privilegios | Lo usa |
|---|---|---|
| `willwebs_migrator` | ALL sobre `willwebs` (y `willwebs_test` en dev) | Solo el job `migrate` (Alembic + seeds) y los tests |
| `willwebs_app` | SELECT, INSERT, UPDATE, DELETE | La API en ejecución |

## Paleta de marca

| Color | Hex | Uso |
|---|---|---|
| Azul marino oscuro | `#09274F` | Fondos oscuros (navbar, hero, footer) |
| Azul medio | `#094183` | Títulos y acentos |
| Azul vivo | `#014DBF` | Primario / CTA |

Definidos en `frontend/app/styles/main.scss`. La landing estática original quedó en el historial de git
(commit `4d58ea4`, `frontend/legacy/`).
