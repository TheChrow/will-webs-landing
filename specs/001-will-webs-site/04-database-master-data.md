# 04 — MySQL: modelos de datos y documento Master Data

## Objetivo
Definir el modelo de datos del sitio y un **documento de Master Data** (`docs/master-data.md`) que sea la fuente de verdad de entidades, campos, reglas y dueños de cada dato.

## Decisiones técnicas
- **MySQL 8.4 LTS**, motor InnoDB, charset `utf8mb4`, collation `utf8mb4_0900_ai_ci`, zona horaria UTC en DB (conversión a `America/Santiago` en la capa de presentación).
- ORM **SQLAlchemy 2.x** + migraciones **Alembic** (ningún cambio de esquema manual).
- Claves primarias `BIGINT UNSIGNED AUTO_INCREMENT` internas + `public_id CHAR(26)` (ULID) para exponer en la API (no se filtran IDs secuenciales).
- Columnas de auditoría en todas las tablas: `created_at`, `updated_at`, `created_by`, `updated_by`.
- *Soft delete* (`deleted_at`) en contenido; borrado físico/anonimización en datos personales según política de retención.
- Usuario de aplicación con **mínimo privilegio** (`SELECT, INSERT, UPDATE, DELETE` sobre el schema; sin `DROP`, `GRANT`, `FILE`). Usuario separado para migraciones.

## Clasificación de datos

| Tipo | Entidades | Dueño | Cambia |
|---|---|---|---|
| **Master data** (catálogos/contenido) | servicios, categorías, banners, empresas/clientes, bloques de contenido, páginas legales, ajustes | Marketing / Admin | Poco frecuente |
| **Transaccional** | mensajes de contacto (leads), registros de consentimiento | Comercial | Continuo |
| **Seguridad/sistema** | usuarios admin, roles, sesiones/refresh tokens, audit log | TI | Continuo |

## Modelo lógico (v1)

```
service_category 1───* service
banner
client_company
content_block            (clave → texto: misión, visión, CTA, hero...)
legal_document 1───* legal_document_version
site_setting             (clave → valor: email de contacto, redes, etc.)

contact_message *───1 service (opcional: servicio de interés)
consent_record  *───1 legal_document_version

admin_user *───* role  (admin_user_role)
refresh_token  *───1 admin_user
audit_log      *───1 admin_user
```

## Diccionario de datos (resumen — el detalle va en `docs/master-data.md`)

### `service` (Servicios Digitales — hoy 10 en la landing)
| Campo | Tipo | Regla |
|---|---|---|
| id | BIGINT UNSIGNED PK | interno |
| public_id | CHAR(26) UNIQUE | ULID |
| category_id | FK → service_category | nullable |
| slug | VARCHAR(120) UNIQUE | `^[a-z0-9-]+$` |
| title | VARCHAR(120) NOT NULL | |
| summary | VARCHAR(280) NOT NULL | texto de la card |
| description | TEXT | detalle (futura página de servicio) |
| icon | VARCHAR(64) | nombre de ícono del set elegido |
| sort_order | SMALLINT NOT NULL DEFAULT 0 | |
| is_published | BOOLEAN NOT NULL DEFAULT FALSE | |
| + auditoría / deleted_at | | |

### `banner` (slider del hero)
`id, public_id, title, subtitle, image_url, image_alt (NOT NULL — accesibilidad), cta_label, cta_href, sort_order, is_published, starts_at, ends_at, auditoría`

### `client_company` (cinta "Empresas que confían en nosotros")
`id, public_id, name, logo_url, logo_alt, website_url, sort_order, is_published, auditoría` — requiere **autorización de uso de marca** del cliente (campo `logo_consent_at`).

### `content_block`
`id, key (UNIQUE, ej. 'about.mission'), locale (DEFAULT 'es-CL'), title, body (TEXT, Markdown sanitizado), auditoría` — UNIQUE(`key`, `locale`).

### `legal_document` / `legal_document_version`
`legal_document: id, type ENUM('privacy','cookies','terms','accessibility'), slug`
`legal_document_version: id, document_id, version (semver), body, published_at, is_current` — se versiona para poder probar qué texto aceptó cada usuario.

### `contact_message` (lead del formulario)
| Campo | Tipo | Regla |
|---|---|---|
| id / public_id | | |
| name | VARCHAR(120) NOT NULL | dato personal |
| email | VARCHAR(254) NOT NULL | dato personal, validado RFC 5322 |
| company | VARCHAR(160) | |
| phone | VARCHAR(32) | opcional, E.164 |
| service_id | FK nullable | servicio de interés |
| message | TEXT NOT NULL | máx. 5000 caracteres |
| status | ENUM('new','read','contacted','archived','spam') | |
| consent_record_id | FK NOT NULL | sin consentimiento no se guarda |
| ip_hash | BINARY(32) | SHA-256 + pepper (no IP en claro) |
| user_agent | VARCHAR(255) | truncado |
| created_at | DATETIME(6) | |
| retention_until | DATE | para purga automática |

### `consent_record`
`id, legal_document_version_id, purpose ENUM('contact','marketing','analytics_cookies'), granted BOOLEAN, granted_at, ip_hash, subject_email_hash`

### `admin_user`, `role`, `admin_user_role`, `refresh_token`, `audit_log`
- `admin_user`: `email UNIQUE, password_hash (Argon2id), is_active, mfa_secret (cifrado), last_login_at, failed_attempts, locked_until`
- `refresh_token`: `token_hash, expires_at, revoked_at, user_agent, ip_hash`
- `audit_log`: `actor_id, action, entity, entity_id, diff JSON, ip_hash, created_at` (append-only)

## Reglas de Master Data
- Cada entidad maestra tiene **dueño**, **ciclo de vida** (borrador → publicado → archivado) y **reglas de validación** documentadas.
- Seeds iniciales generados desde el contenido actual de la landing (10 servicios, 3 banners, misión/visión, logos placeholder).
- Retención: leads 24 meses desde el último contacto (a confirmar con negocio/legal), luego anonimización; logs de auditoría 12 meses.

## Entregables
- `docs/master-data.md` (diccionario completo, dueños, reglas, retención) + diagrama ER (Mermaid).
- Modelos SQLAlchemy + migración Alembic inicial.
- `db/seeds/` con master data inicial.

## Criterios de aceptación
- [ ] `alembic upgrade head` crea el esquema desde cero; `downgrade` funciona.
- [ ] Seeds reproducen exactamente el contenido actual de la landing.
- [ ] Diagrama ER y diccionario revisados y aprobados.
- [ ] Usuario de app sin privilegios DDL.
