# 05 — Backend en FastAPI

## Objetivo
API REST que sirva el contenido del sitio, reciba los leads del formulario y exponga un panel admin mínimo.

## Stack
- **Python 3.12**, **FastAPI**, **Pydantic v2** (+ `pydantic-settings` para configuración por entorno).
- **SQLAlchemy 2.x** async + driver `asyncmy` (o `aiomysql`), **Alembic**.
- Servidor: Uvicorn (dev) / Gunicorn + UvicornWorker (prod).
- Gestión de dependencias: **uv** con `uv.lock` (versiones fijadas).
- Calidad: `ruff` (lint+format), `mypy`, `pytest` + `httpx` + testcontainers MySQL.

## Estructura

```
backend/app/
├── main.py              # app factory, middlewares, routers
├── core/                # config, security, logging, rate limit
├── db/                  # engine, session, base
├── models/              # SQLAlchemy
├── schemas/             # Pydantic (entrada/salida separadas)
├── repositories/        # acceso a datos
├── services/            # lógica de negocio (email, captcha, leads)
└── api/v1/
    ├── public/          # services, banners, clients, content, legal, contact
    └── admin/           # auth, CRUD de contenido, leads
```

## Endpoints v1

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/v1/health` | — | liveness / readiness (incluye ping DB) |
| GET | `/api/v1/services` | — | servicios publicados, ordenados |
| GET | `/api/v1/banners` | — | banners vigentes |
| GET | `/api/v1/clients` | — | empresas publicadas |
| GET | `/api/v1/content/{key}` | — | bloque de contenido |
| GET | `/api/v1/legal/{type}` | — | versión vigente del documento legal |
| POST | `/api/v1/contact` | captcha | crea lead + consentimiento, envía correo |
| POST | `/api/v1/admin/auth/login` | — | login (rate limit estricto) |
| POST | `/api/v1/admin/auth/refresh` · `/logout` | cookie | rotación de refresh token |
| CRUD | `/api/v1/admin/{services,banners,clients,content,legal}` | admin | gestión de master data |
| GET/PATCH | `/api/v1/admin/contact-messages` | admin | bandeja de leads, cambio de estado |

- Respuestas públicas cacheables (`Cache-Control` + `ETag`); el frontend puede prerenderizarlas en build.
- Errores en formato uniforme **RFC 9457 (Problem Details)**; nunca stack traces al cliente.
- OpenAPI/Swagger habilitado solo en dev (`docs_url=None` en prod) o protegido.
- Paginación por cursor/limit con `limit` máximo (ej. 100).

## Flujo `POST /contact`
1. Validación Pydantic estricta (longitudes, email, `extra="forbid"`).
2. Verificación de captcha (Turnstile) server-side + campo honeypot vacío + tiempo mínimo de llenado.
3. Rate limit por IP (ej. 5/hora) y por email.
4. Transacción: `consent_record` + `contact_message`.
5. Correo de notificación **asíncrono** (tarea en background / cola), con escape de contenido y sin inyección de cabeceras.
6. Respuesta `202 Accepted` genérica (no revela si el email ya existe).

## Autenticación admin
- Contraseñas con **Argon2id**; bloqueo progresivo tras intentos fallidos.
- Access token JWT corto (≤15 min) + refresh token rotativo en cookie `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/admin/auth`.
- **MFA TOTP** recomendado para admins.
- RBAC por roles (`admin`, `editor`), dependencias FastAPI por endpoint.
- Toda escritura admin genera `audit_log`.

## Observabilidad
- Logs JSON estructurados con `request_id` (cabecera `X-Request-ID`), sin datos personales en claro.
- Métricas básicas (Prometheus `/metrics` interno) — opcional v1.

## Entregables
- Código en `backend/`, Dockerfile, tests con cobertura ≥ 80 % en servicios y endpoints.
- Colección de pruebas de API (OpenAPI exportado / Postman).

## Criterios de aceptación
- [ ] Todos los endpoints públicos responden < 100 ms p95 en local.
- [ ] `POST /contact` rechaza spam (sin captcha, honeypot lleno, exceso de rate).
- [ ] Ninguna consulta SQL construida por concatenación de strings (revisión + regla de lint).
- [ ] Tests de integración contra MySQL real en CI.
