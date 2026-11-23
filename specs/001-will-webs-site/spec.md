# Spec 001 — Will-Webs Site

> Estado: **Borrador** · Fecha: 2026-11-23 · Base: landing estática `will-webs-landing` (Bootstrap 5, one-page)

## 1. Objetivo

Evolucionar la landing estática actual a un **sitio web completo** para Will-Webs:

- Frontend en **React** que preserve la marca y la estructura de la landing (hero/slider, servicios, CTA, misión/visión, cinta de empresas, contacto, footer).
- **Backend en FastAPI** que sirva el contenido (servicios, banners, logos, textos) y reciba los leads del formulario de contacto.
- **MySQL** como base de datos, con un modelo de datos documentado (Master Data).
- **Seguridad** desde el diseño (OWASP Top 10) y **políticas web** (privacidad, cookies, términos, accesibilidad) conformes a la ley chilena.
- **Docker** desde el primer commit: todo el stack se levanta con un solo comando.

## 2. Alcance

| Incluido (v1) | Fuera de alcance (v1) |
|---|---|
| Sitio público (one-page + páginas legales) | E-commerce / pagos |
| Formulario de contacto persistido + notificación por correo | Blog / CMS completo (se evalúa en v2) |
| Panel admin mínimo (CRUD de contenido y bandeja de leads) | Multi-idioma (se deja preparado, i18n en v2) |
| API REST versionada `/api/v1` | App móvil |
| Docker Compose dev + prod | Kubernetes |

## 3. Arquitectura objetivo

```
           Internet
              │  HTTPS (TLS)
        ┌─────▼──────┐
        │  proxy     │  Caddy/Nginx: TLS, headers de seguridad, rate limit, gzip
        └──┬──────┬──┘
   /       │      │  /api/*
 ┌─────────▼┐   ┌─▼──────────┐      ┌──────────┐
 │ frontend │   │  backend   │─────▶│  MySQL   │  (red interna, sin puerto público)
 │ React    │   │  FastAPI   │      │  8.4 LTS │
 │ (estático│   │  Uvicorn   │      └──────────┘
 │  Nginx)  │   └────────────┘
 └──────────┘
```

Un solo dominio (`/` frontend, `/api` backend) → sin CORS en producción y cookies `SameSite=Strict`.

## 4. Estructura de repositorio propuesta (monorepo)

```
will-webs/
├── frontend/            # React + Vite + TypeScript
├── backend/             # FastAPI + SQLAlchemy + Alembic
├── db/                  # init scripts, seeds de master data
├── proxy/               # Caddyfile / nginx.conf
├── docs/                # master-data.md, ADRs, políticas
├── specs/               # este directorio
├── docker-compose.yml           # base
├── docker-compose.dev.yml       # hot reload, puertos locales
├── docker-compose.prod.yml      # imágenes inmutables, sin bind mounts
└── .env.example
```

La landing actual (`index.html`, `styles.css`) se conserva como **referencia visual** hasta que el frontend React alcance paridad.

## 5. Sub-tareas

| # | Sub-tarea | Documento | Depende de |
|---|---|---|---|
| 6 | Dockerización desde el inicio | [06-docker.md](06-docker.md) | — (va primero) |
| 4 | MySQL — modelos de datos y Master Data | [04-database-master-data.md](04-database-master-data.md) | 6 |
| 5 | Backend FastAPI | [05-backend-fastapi.md](05-backend-fastapi.md) | 4, 6 |
| 1 | Revisión Frontend, UX/UI, tecnologías React | [01-frontend-ux-ui.md](01-frontend-ux-ui.md) | 6 (5 para integrar) |
| 2 | Seguridad (hacking, SQLi, malware, peticiones) | [02-security.md](02-security.md) | transversal a 1, 4, 5, 6 |
| 3 | Políticas web | [03-web-policies.md](03-web-policies.md) | 1, 4 (consentimientos) |

### Orden de ejecución sugerido

1. **Fase 0 — Cimientos:** monorepo + Docker Compose (6) + esqueleto FastAPI con `/health` + MySQL + Alembic vacío.
2. **Fase 1 — Datos y API:** Master Data (4) → modelos + migraciones + seeds → endpoints públicos y de contacto (5).
3. **Fase 2 — Frontend:** auditoría UX/UI de la landing → migración a React con paridad visual → integración con API (1).
4. **Fase 3 — Endurecimiento:** checklist de seguridad (2), políticas y banner de consentimiento (3), admin mínimo.
5. **Fase 4 — Release:** pruebas E2E, Lighthouse/axe, escaneo de imágenes, despliegue prod.

La seguridad (2) no es una fase aislada: cada sub-tarea incluye sus controles y la fase 3 los verifica.

## 6. Criterios de aceptación globales

- `docker compose up` levanta todo el stack en local sin pasos manuales (salvo copiar `.env.example`).
- Paridad visual con la landing actual, responsive 360 px → 1440 px.
- Lighthouse ≥ 90 en Performance, Accessibility, Best Practices y SEO (móvil).
- WCAG 2.2 AA sin errores críticos en axe.
- Formulario de contacto: lead guardado en MySQL, correo de notificación enviado, protegido contra spam y abuso.
- 0 vulnerabilidades *high/critical* en `pip-audit`, `npm audit` y escaneo de imágenes (Trivy).
- Cabeceras de seguridad con nota **A** en securityheaders.com.
- Políticas de privacidad, cookies y términos publicadas y enlazadas desde el footer.

## 7. Decisiones abiertas (requieren definición del negocio)

1. **Hosting/destino de despliegue**: VPS (Docker Compose) vs. cloud gestionado (DB gestionada).
2. **Proveedor de correo** para notificaciones (SMTP propio, Google Workspace, SendGrid/Resend, SES).
3. **Anti-spam**: Cloudflare Turnstile (recomendado) vs. hCaptcha vs. solo honeypot + rate limit.
4. **Analítica**: ninguna, Plausible/Umami (sin cookies, recomendado) o Google Analytics (requiere consentimiento).
5. **Panel admin en v1**: sí (mínimo) o dejar contenido como seeds/SQL hasta v2.
6. **Razón social, RUT y datos del responsable de datos** para las políticas legales.
