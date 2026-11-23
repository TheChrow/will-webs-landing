# Traspaso — Will-Webs Site

> Documento para quien continúe el proyecto (incluidas sesiones de Claude Code en la nube).
> Actualizado: 2026-11-23 · Rama: `feat/fase-0-cimientos` · Remoto: `origin` (GitHub `will-webs-landing`).

Léelo completo antes de tocar código. Te dice qué hay, cómo levantarlo, cómo desplegarlo y qué falta.

---

## 1. Estado en una mirada

| Fase | Contenido | Estado | Commit |
|---|---|---|---|
| 0 — Cimientos | Monorepo, Docker Compose dev/prod, FastAPI base, MySQL, proxy Caddy | ✅ | `4d58ea4` |
| 1 — Datos y API | Master Data, 15 tablas, migración Alembic, seeds, API pública, `POST /contact` | ✅ | `d8eb4be` |
| 2 — Frontend | React Router v8 pre-renderizado, formulario, páginas legales, CSP estricta | ✅ | `9e40d4f` |
| 3 — Endurecimiento | Panel admin (auth + CRUD + leads + legal + auditoría), derechos del titular, retención, borradores legales, escaneos, CI | ✅ | commit "Fase 3" (último de la rama) |
| 4 — Release | E2E, Lighthouse/axe, ZAP, despliegue a producción, MFA | ⏳ **pendiente** | — |

**La rama `main` del remoto todavía no tiene este trabajo** (solo la landing original). Trabaja sobre
`feat/fase-0-cimientos` o mézclala a `main` cuando se apruebe.

```bash
git fetch origin
git switch feat/fase-0-cimientos
```

Pruebas al cierre de la Fase 3: **50 tests backend** (unitarios + integración contra MySQL real) y
**7 tests frontend**, todos en verde; `ruff`, `tsc`, `pip-audit`, `npm audit`, `hadolint` y `gitleaks` limpios.

---

## 2. Documentos que debes conocer

| Documento | Para qué |
|---|---|
| [specs/001-will-webs-site/spec.md](../specs/001-will-webs-site/spec.md) | Spec general, alcance, fases, criterios de aceptación y **decisiones abiertas** |
| [specs/001-will-webs-site/0X-*.md](../specs/001-will-webs-site/) | Spec por sub-tarea (frontend, seguridad, políticas, datos, backend, docker) |
| [docs/master-data.md](master-data.md) | Modelo de datos: diccionario, ER, reglas, retención. **Todo cambio de esquema se refleja aquí en el mismo commit** |
| [docs/security.md](security.md) | Modelo de amenazas, checklist ASVS, resultados de escaneo, riesgos aceptados, pendientes |
| [docs/ux-audit.md](ux-audit.md) | Hallazgos UX/UI y cómo se resolvieron |
| [README.md](../README.md) | Comandos del día a día |

---

## 3. Arquitectura

```
 Internet ──HTTPS──▶ proxy (Caddy 2.11)  ── TLS automático, cabeceras de seguridad, body ≤ 1 MB
                       │ /            │ /api/*
                       ▼              ▼
              frontend (Nginx 1.30   backend (FastAPI, Gunicorn+Uvicorn, Python 3.12)
              sin privilegios,         │  red "internal" (sin salida a Internet en prod)
              HTML pre-renderizado)    ▼
                                    db (MySQL 8.4)   ← job "migrate" (Alembic + seeds) corre antes del backend
```

| Capa | Tecnología | Carpeta |
|---|---|---|
| Frontend | React 19, React Router v8 (`ssr:false` + `prerender`), Vite 8, TypeScript 5.9, Bootstrap 5.3 SCSS, TanStack Query, React Hook Form + Zod | `frontend/` |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 async + asyncmy, Alembic, PyJWT, argon2-cffi; dependencias con **uv** (`uv.lock`) | `backend/` |
| Datos | MySQL 8.4, `utf8mb4`, UTC | `db/init/` (usuario de app solo DML) |
| Proxy | Caddy | `proxy/Caddyfile` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |

Decisiones clave que **no** debes romper:
- **Mismo origen**: `/` frontend y `/api` backend detrás del mismo proxy → sin CORS en prod, cookies `SameSite=Strict`.
- **CSP sin `'unsafe-inline'`**: `frontend/scripts/csp.mjs` calcula en el build los hashes de los scripts inline y Nginx los envía. **No uses `style="..."` en JSX** (el HTML pre-renderizado lo bloquearía); usa clases.
- **Contenido de respaldo**: `frontend/app/lib/fallback.ts` replica los seeds (`backend/app/seeds.py`) para el HTML pre-renderizado. Si cambias los seeds, actualízalo.
- **IDs públicos** son ULID (`public_id`); nunca expongas el `id` interno.
- **Dos usuarios MySQL**: `willwebs_app` (solo DML, lo usa la API) y `willwebs_migrator` (DDL, solo Alembic/seeds/tests).
- **Versiones legales publicadas son inmutables** (prueba del consentimiento).

---

## 4. Levantar en desarrollo

### 4.1 Con Docker (recomendado; así se desarrolló)

Requisitos: Docker con Compose v2.

```bash
cp .env.example .env            # en Windows: copy .env.example .env
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

| URL | Qué es |
|---|---|
| http://localhost:8088 | Sitio (vía proxy) |
| http://localhost:8088/admin | Panel admin |
| http://localhost:8001/api/docs | Swagger (solo dev) |
| http://localhost:8025 | Mailpit (correos de prueba) |
| `localhost:3307` | MySQL (solo 127.0.0.1) |

Crear tu usuario del panel (pide la contraseña, mínimo 12 caracteres):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend \
  python -m app.cli create-admin --email tu@empresa.cl --name "Tu Nombre" --role admin
```

Tests y calidad:

```bash
DC="docker compose -f docker-compose.yml -f docker-compose.dev.yml"
$DC run --rm migrate pytest            # backend: corre en "migrate" (tiene permisos DDL sobre willwebs_test)
$DC run --rm migrate ruff check .
$DC exec frontend npm test
$DC exec frontend npm run typecheck
```

> La base `willwebs_test` la crea `db/init/01-app-user.sh` solo al **crear** el volumen de MySQL. Si tu
> volumen es anterior y falta, créala como root (`CREATE DATABASE willwebs_test …; GRANT ALL ON willwebs_test.* TO 'willwebs_migrator'@'%';`)
> o recrea el volumen (`down -v`, borra los datos locales).

### 4.2 Sin Docker (p. ej. una sesión en la nube sin Docker)

Necesitas Python 3.12 + [uv](https://docs.astral.sh/uv/) 0.13.x, Node 22 y un MySQL 8.4 accesible.

```bash
# Backend
cd backend
uv sync --frozen
export DB_HOST=127.0.0.1 DB_NAME=willwebs_test \
       MIGRATOR_DB_USER=willwebs_migrator MIGRATOR_DB_PASSWORD=<clave>
uv run pytest -q          # el conftest migra, siembra y crea usuarios de prueba en <DB_NAME>_test
uv run ruff check .

# Frontend
cd ../frontend
npm ci
npm run typecheck && npm test && npm run build
```

El workflow `.github/workflows/ci.yml` hace exactamente esto con un servicio MySQL: úsalo como
referencia. **Nota:** el CI se escribió pero **nunca se ha ejecutado** en GitHub; revisa la primera corrida.

---

## 5. Desplegar la versión actual (producción)

Objetivo: un servidor Linux con Docker (VPS) sirviendo el sitio con TLS. Todo corre con Docker Compose.

### 5.1 Requisitos previos

- [ ] Servidor Linux (2 vCPU / 2 GB RAM mínimo) con Docker Engine + Compose v2.
- [ ] Dominio con registro **A/AAAA** apuntando al servidor (Caddy emite el certificado solo).
- [ ] Firewall: abiertos solo **22 (SSH con llave), 80 y 443** (TCP; 443/UDP para HTTP/3).
- [ ] Proveedor SMTP (host, puerto, usuario, contraseña) para el aviso de leads.
- [ ] Cuenta Cloudflare con un widget **Turnstile** para el dominio (clave de sitio pública + clave secreta).
- [ ] Datos legales del negocio: razón social, RUT, domicilio, email de privacidad (para publicar las políticas).

### 5.2 Código y configuración

```bash
git clone https://github.com/TheChrow/will-webs-landing.git willwebs && cd willwebs
git switch feat/fase-0-cimientos     # o main, si ya se mezcló
cp .env.example .env
```

Edita `.env` (valores **no secretos**):

| Variable | Valor en producción |
|---|---|
| `APP_ENV` | `production` |
| `SITE_ADDRESS` | tu dominio, p. ej. `willwebs.cl` (sin `https://`) |
| `ALLOWED_HOSTS` | `willwebs.cl,localhost,127.0.0.1,backend` |
| `VITE_SITE_URL` | `https://willwebs.cl` (canonical y Open Graph; se incrusta en el build) |
| `VITE_TURNSTILE_SITE_KEY` | clave de **sitio** (pública) de Turnstile |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_STARTTLS` | datos del proveedor (`SMTP_STARTTLS=true` para 587) |
| `MAIL_FROM` | `Will-Webs <no-reply@willwebs.cl>` |
| `LEADS_NOTIFY_TO` | buzón que recibe los leads |
| `MYSQL_DATABASE` / `MIGRATOR_DB_USER` / `APP_DB_USER` | dejar los de ejemplo salvo que quieras otros nombres |
| `MYSQL_ROOT_PASSWORD`, `MIGRATOR_DB_PASSWORD`, `APP_DB_PASSWORD`, `TURNSTILE_SECRET_KEY` | **dejar vacíos**: en prod van en `secrets/` |

### 5.3 Secretos (Docker secrets, archivos de una línea, nunca en git)

```bash
mkdir -p secrets && chmod 700 secrets
gen() { openssl rand -base64 48 | tr -d '\n' > "secrets/$1"; }
gen mysql_root_password
gen migrator_db_password
gen app_db_password
gen hash_pepper          # seudonimiza IPs/emails: NO cambiarlo después (rompe la búsqueda por titular)
gen jwt_secret           # cambiarlo invalida todas las sesiones del panel
printf '%s' '<CLAVE SECRETA TURNSTILE>' > secrets/turnstile_secret_key
printf '%s' '<CONTRASEÑA SMTP>'         > secrets/smtp_password
chmod 600 secrets/*
```

> ⚠️ Respáldalos fuera del servidor (gestor de contraseñas). Sin `hash_pepper` no se puede atender
> una solicitud de derechos sobre consentimientos ya registrados.

### 5.4 Levantar

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

Al arrancar: MySQL se inicializa (crea los usuarios), el job `migrate` aplica Alembic + seeds y luego
arrancan backend, frontend y proxy. Caddy obtiene el certificado TLS en el primer acceso.

> El build del frontend corre `typecheck` + tests + `build` + `csp.mjs`; si falla un test, el despliegue falla (a propósito).

### 5.5 Puesta en marcha

1. **Crear el primer admin** (contraseña fuerte, 12+ caracteres):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
     python -m app.cli create-admin --email admin@willwebs.cl --name "Nombre" --role admin
   ```
2. **Publicar las políticas legales** en `https://<dominio>/admin` → Legal: abrir cada versión `0.2.0`,
   completar los datos entre `[CORCHETES]` (el panel no permite publicar si quedan), revisar con
   asesoría legal y **Publicar**. Hasta entonces la Privacidad vigente es la `0.1.0` provisional.
3. **Contenido**: en Contenido, escribir y publicar Misión y Visión; en Servicios, revisar textos.
4. **Datos públicos**: ajustar `contact.email` (hoy `contacto@example.com`) vía
   `PUT /api/v1/admin/settings/contact.email` (aún no hay pantalla de ajustes; ver pendientes).
5. **Job de retención diario** (cron del host):
   ```cron
   15 3 * * * cd /ruta/willwebs && docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backend python -m app.jobs.retention >> /var/log/willwebs-retention.log 2>&1
   ```
6. **Backups de MySQL** (pendiente de automatizar; mínimo diario):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
     sh -c 'exec mysqldump -uroot -p"$(cat /run/secrets/mysql_root_password)" --single-transaction --databases willwebs' \
     | gzip > backup-$(date +%F).sql.gz
   ```
   Cifra y copia fuera del servidor. **Prueba una restauración** antes de darlo por bueno.

### 5.6 Verificación post-despliegue

```bash
D=https://willwebs.cl
curl -s $D/api/v1/health/ready                 # {"status":"ok","database":"up"}
curl -sI $D/ | grep -iE 'strict-transport|content-security|x-frame'
curl -s -o /dev/null -w '%{http_code}\n' $D/no-existe   # 404
curl -s -o /dev/null -w '%{http_code}\n' $D/api/docs    # 404 (Swagger apagado en prod)
```

- [ ] El sitio carga por HTTPS y el formulario muestra el widget Turnstile.
- [ ] Un envío de prueba llega al buzón `LEADS_NOTIFY_TO` y aparece en `/admin`.
- [ ] Consola del navegador sin violaciones de CSP (si Turnstile inyecta estilos y la CSP los bloquea, ajustar `style-src` en `frontend/scripts/csp.mjs`).
- [ ] securityheaders.com y SSL Labs con nota A.

### 5.7 Actualizar una versión ya desplegada

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --pull always
```
Las migraciones se aplican solas (job `migrate`). Antes de una migración destructiva, haz backup.

---

## 6. Variables y secretos — referencia completa

| Nombre | Dónde | Obligatoria en prod | Descripción |
|---|---|---|---|
| `APP_ENV` | `.env` | sí | `development` / `production` |
| `SITE_ADDRESS` | `.env` | sí | Dirección que sirve Caddy (`:80` en dev, dominio en prod) |
| `HTTP_PORT`, `API_PORT_LOCAL`, `DB_PORT_LOCAL` | `.env` | no (solo dev) | Puertos locales (8088, 8001, 3307) |
| `MYSQL_DATABASE`, `MIGRATOR_DB_USER`, `APP_DB_USER` | `.env` | sí | Nombres de base y usuarios |
| `ALLOWED_HOSTS` | `.env` | sí | Hosts aceptados por la API (TrustedHost) |
| `CORS_ORIGINS` | `.env` | no | Solo dev (Vite directo); vacío en prod |
| `SMTP_*`, `MAIL_FROM`, `LEADS_NOTIFY_TO` | `.env` | sí | Correo de aviso de leads |
| `VITE_SITE_URL`, `VITE_TURNSTILE_SITE_KEY` | `.env` (build) | sí | Públicas; se incrustan en el JS |
| `mysql_root_password`, `migrator_db_password`, `app_db_password` | `secrets/` | sí | MySQL |
| `hash_pepper` | `secrets/` | sí | Seudonimización HMAC (no rotar) |
| `jwt_secret` | `secrets/` | sí | Firma de los JWT del panel (32+ bytes) |
| `turnstile_secret_key` | `secrets/` | sí | Verificación anti-bots server-side |
| `smtp_password` | `secrets/` | si el SMTP usa auth | |

Ajustes opcionales del backend (`backend/app/core/config.py`): `ACCESS_TOKEN_MINUTES` (15),
`REFRESH_TOKEN_DAYS` (7), `LOGIN_MAX_ATTEMPTS` (5), `LOGIN_LOCK_MINUTES` (15),
`LEAD_RETENTION_MONTHS` (24), `AUDIT_RETENTION_MONTHS` (12), `CONTACT_RATE_LIMIT_PER_HOUR` (5),
`CONTACT_MIN_FILL_SECONDS` (3).

---

## 7. Lo que falta (priorizado)

### 7.1 Bloqueantes para salir a producción
1. **Decisiones de negocio** (ver `spec.md` §7): hosting, dominio, proveedor SMTP, Turnstile, razón social/RUT.
2. **Revisión legal** y publicación de las 4 políticas (`backend/app/legal/*.md` → panel).
3. **Mezclar la rama a `main`** (o definir la rama de despliegue) y verificar que el **CI pase** en GitHub
   (nunca se ha ejecutado; las versiones de las *actions* pueden necesitar ajuste).
4. **Backups automáticos** de MySQL cifrados + prueba de restauración.
5. **Job de retención** programado (cron).
6. Contenido real: Misión/Visión, textos de servicios, `contact.email`, imágenes de banners/logos con autorización.

### 7.2 Fase 4 — Release (de la spec)
- [ ] Pruebas **E2E con Playwright** (home, formulario, panel) + **axe** automatizado.
- [ ] **Lighthouse** móvil ≥ 90 en las 4 categorías (no medido aún). El CSS pesa ~155 KB sin comprimir: candidato a recortar utilidades de Bootstrap.
- [ ] **OWASP ZAP** baseline contra staging en CI.
- [ ] `sitemap.xml` (necesita el dominio) y `security.txt` (necesita email de seguridad).
- [ ] Verificar **Turnstile real** en el navegador (en dev está desactivado) y su compatibilidad con la CSP.

### 7.3 Seguridad pendiente (ver `docs/security.md` §5)
- [ ] **MFA TOTP** para el rol `admin` (la columna `admin_user.mfa_secret_enc` ya existe).
- [ ] Rate limiting en el proxy (Caddy necesita el plugin `caddy-ratelimit`, requiere imagen propia con `xcaddy`) o Cloudflare delante. Hoy el límite está solo en la app y es **por proceso**.
- [ ] Alertas sobre `login_failed`, `refresh_reuse_detected`, picos de 429/5xx.
- [ ] Revisar `.trivyignore` (CVE de nginx aceptado temporalmente) y reconstruir con `--pull` cuando salga nginx 1.30.7.

### 7.4 Panel admin — mejoras
- [ ] Pantallas para **banners, empresas y ajustes** (la API ya existe: `/api/v1/admin/{banners,clients,settings}`).
- [ ] Crear servicios desde la UI (hoy solo editar/publicar; crear es por API).
- [ ] Pantalla de **derechos del titular** (hoy solo API: `/api/v1/admin/data-subject/{export,anonymize}`).
- [ ] Gestión de usuarios del panel (hoy solo CLI) y cambio de contraseña.
- [ ] Subida de imágenes (ver ASVS V12 en `docs/security.md`: magic bytes, re-encode, ClamAV).

---

## 8. Problemas conocidos y trampas

| Síntoma | Causa | Solución |
|---|---|---|
| `port is already allocated` al levantar | Otro servicio usa 8080/8000/3306 | Cambiar `HTTP_PORT`, `API_PORT_LOCAL`, `DB_PORT_LOCAL` en `.env` |
| El frontend en dev sirve HTML viejo o rutas nuevas dan 404 | Las imágenes dev y prod del frontend comparten la etiqueta `willwebs-frontend`; quedó corriendo la de prod | `docker compose ... up -d --build frontend` con el overlay correcto |
| 504 en `/node_modules/.vite/deps/...` | Vite re-optimizando dependencias o sin permisos en `node_modules` | Ya mitigado (`optimizeDeps.include` + `chown` en el Dockerfile). Si reaparece: `docker volume rm willwebs_frontend_node_modules` y rebuild |
| Cambios en archivos no recargan (Windows) | Docker Desktop no propaga eventos de archivos | Ya mitigado con `VITE_USE_POLLING=1` |
| Tests fallan por `email-validator` | Rechaza dominios reservados (`.local`) | Usar `@example.com` en datos de prueba |
| Tests de contenido público fallan tras tests admin | La base de tests es compartida en la sesión | Comprobar registros sembrados concretos, no listas vacías |
| `mysqladmin`/healthcheck en prod | Con `_FILE` las contraseñas no están en el entorno | El healthcheck usa `ping` sin credenciales a propósito |
| Seeds no actualizan textos existentes | Son idempotentes **solo-insert** | Editar desde el panel, o una migración de datos |

---

## 9. Convenciones de trabajo

- **Idioma**: código en inglés, textos de UI, docs y mensajes de commit en **español**.
- **Commits** pequeños por fase/tema; mensaje con resumen y viñetas.
- **Esquema**: todo cambio por migración Alembic (`alembic revision --autogenerate`), revisada a mano
  (en MySQL, `downgrade` no puede borrar índices que respaldan FKs antes de la tabla) y reflejada en `docs/master-data.md`.
- **SQL**: solo SQLAlchemy con parámetros; prohibido SQL construido con strings (regla `ruff S608`).
- **Entradas**: Pydantic con `extra="forbid"`; salidas sin IDs internos.
- **Escrituras admin** siempre con `audit.record(...)`.
- **Frontend**: sin `style=""`, sin `dangerouslySetInnerHTML`; Markdown solo con `react-markdown` + `skipHtml`.
- Antes de cada commit: tests backend + frontend en verde, `ruff`, `tsc`.

---

## 10. Mapa rápido de archivos

```
backend/app/
  main.py                    app factory, middlewares, manejadores de error
  core/config.py             todas las variables de entorno y validación de secretos en prod
  core/security.py           Argon2id, JWT, refresh tokens
  api/v1/public/             API pública (contenido, contacto)
  api/v1/admin/              panel: auth, content, leads (+ derechos del titular), legal (+ auditoría)
  services/                  leads, captcha, mailer, audit, privacy (anonimización)
  models/                    SQLAlchemy (ver docs/master-data.md)
  seeds.py · legal/*.md      master data inicial y borradores legales
  cli.py · jobs/retention.py crear admin · job de retención
backend/migrations/          Alembic
backend/tests/               pytest (conftest prepara la base de tests)
frontend/app/
  routes/ · routes/admin/    páginas públicas · panel
  components/ · admin/       secciones del sitio · cliente y UI del panel
  lib/                       API pública, queries, Zod, contenido de respaldo, SEO
frontend/scripts/csp.mjs     CSP con hashes
proxy/Caddyfile · frontend/nginx.conf · docker-compose*.yml
```
