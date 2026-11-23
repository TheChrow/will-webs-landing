# Master Data — Will-Webs Site

> Versión 1.0 · 2026-11-23 · Fuente de verdad del modelo de datos. Todo cambio de esquema se hace
> vía migración Alembic **y** se refleja aquí en el mismo PR.

## 1. Convenciones

| Tema | Regla |
|---|---|
| Motor | MySQL 8.4 LTS, InnoDB, `utf8mb4` / `utf8mb4_0900_ai_ci` |
| Fechas | `DATETIME(6)` en **UTC**; conversión a `America/Santiago` en presentación |
| Claves | `id BIGINT UNSIGNED AUTO_INCREMENT` interno; `public_id CHAR(26)` (ULID) es lo único que expone la API |
| Nombres | tablas y columnas en `snake_case` singular; constraints con naming convention (`pk_`, `fk_`, `uq_`, `ix_`, `ck_`) |
| Auditoría | toda tabla de negocio tiene `created_at`, `updated_at`, `created_by`, `updated_by` (FK → `admin_user`, `NULL` = sistema/seed) |
| Borrado | contenido: *soft delete* (`deleted_at`); datos personales: anonimización/borrado físico según retención |
| Publicación | contenido visible solo si `is_published = 1` y `deleted_at IS NULL` (y dentro de la vigencia, si aplica) |
| Datos personales | nunca IP en claro: `ip_hash` = HMAC-SHA256(IP, pepper) |

## 2. Clasificación y dueños

| Dominio | Entidades | Tipo | Dueño | Frecuencia de cambio |
|---|---|---|---|---|
| Catálogo | `service_category`, `service` | Master data | Marketing | Baja |
| Contenido | `banner`, `client_company`, `content_block`, `site_setting` | Master data | Marketing | Baja/media |
| Legal | `legal_document`, `legal_document_version` | Master data | Legal | Baja (versionado) |
| Leads | `contact_message`, `consent_record` | Transaccional · **datos personales** | Comercial | Continua |
| Seguridad | `admin_user`, `role`, `admin_user_role`, `refresh_token`, `audit_log` | Sistema | TI | Continua |

## 3. Diagrama entidad-relación

```mermaid
erDiagram
    service_category ||--o{ service : agrupa
    service ||--o{ contact_message : "interés (opcional)"
    legal_document ||--|{ legal_document_version : versiona
    legal_document_version ||--o{ consent_record : "aceptada en"
    consent_record ||--o| contact_message : respalda
    admin_user ||--o{ admin_user_role : tiene
    role ||--o{ admin_user_role : asignado
    admin_user ||--o{ refresh_token : emite
    admin_user ||--o{ audit_log : actor

    service_category { bigint id PK; char public_id UK; varchar slug UK; varchar name }
    service { bigint id PK; char public_id UK; bigint category_id FK; varchar slug UK; varchar title; varchar summary }
    banner { bigint id PK; char public_id UK; varchar title; varchar image_alt; datetime starts_at; datetime ends_at }
    client_company { bigint id PK; char public_id UK; varchar name; varchar logo_url; datetime logo_consent_at }
    content_block { bigint id PK; varchar key; varchar locale; text body }
    site_setting { bigint id PK; varchar key UK; text value; bool is_public }
    legal_document { bigint id PK; enum type UK; varchar slug UK }
    legal_document_version { bigint id PK; bigint document_id FK; varchar version; bool is_current }
    contact_message { bigint id PK; char public_id UK; varchar email; enum status; bigint consent_record_id FK; date retention_until }
    consent_record { bigint id PK; bigint legal_document_version_id FK; enum purpose; bool granted }
    admin_user { bigint id PK; char public_id UK; varchar email UK; varchar password_hash }
    role { bigint id PK; varchar name UK }
    admin_user_role { bigint admin_user_id PK; bigint role_id PK }
    refresh_token { bigint id PK; bigint admin_user_id FK; binary token_hash UK; datetime expires_at }
    audit_log { bigint id PK; bigint actor_id FK; varchar action; varchar entity; json diff }
```

## 4. Diccionario de datos

Columnas de auditoría (`created_at`, `updated_at`, `created_by`, `updated_by`) se omiten en las tablas para brevedad: aplican a todas salvo `admin_user_role`, `refresh_token`, `consent_record` y `audit_log` (que solo tienen `created_at`).

### 4.1 `service_category`
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id | BIGINT UNSIGNED | no | PK |
| public_id | CHAR(26) | no | UNIQUE, ULID |
| slug | VARCHAR(120) | no | UNIQUE, `^[a-z0-9]+(-[a-z0-9]+)*$` |
| name | VARCHAR(120) | no | |
| sort_order | SMALLINT | no | default 0 |
| deleted_at | DATETIME(6) | sí | soft delete |

### 4.2 `service` — Servicios Digitales
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id / public_id | | no | |
| category_id | BIGINT UNSIGNED | sí | FK → `service_category.id` (ON DELETE SET NULL) |
| slug | VARCHAR(120) | no | UNIQUE, formato slug |
| title | VARCHAR(120) | no | |
| summary | VARCHAR(280) | no | texto de la card |
| description | TEXT | sí | detalle (Markdown, se sanitiza al renderizar) |
| icon | VARCHAR(64) | sí | nombre del ícono (set Lucide/Bootstrap Icons) |
| sort_order | SMALLINT | no | default 0 |
| is_published | BOOL | no | default 0 |
| deleted_at | DATETIME(6) | sí | |

Índice: (`is_published`, `sort_order`).

### 4.3 `banner` — slider del hero
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id / public_id | | no | |
| title | VARCHAR(160) | no | |
| subtitle | VARCHAR(280) | sí | |
| image_url | VARCHAR(500) | sí | ruta relativa o https |
| image_alt | VARCHAR(200) | no | **obligatorio** (WCAG 1.1.1) |
| cta_label | VARCHAR(60) | sí | si hay `cta_label` debe haber `cta_href` |
| cta_href | VARCHAR(500) | sí | `#ancla`, `/ruta` o `https://` (nunca `javascript:`) |
| sort_order | SMALLINT | no | |
| is_published | BOOL | no | |
| starts_at / ends_at | DATETIME(6) | sí | vigencia; `ends_at > starts_at` |
| deleted_at | DATETIME(6) | sí | |

### 4.4 `client_company` — "Empresas que confían en nosotros"
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id / public_id | | no | |
| name | VARCHAR(160) | no | |
| logo_url | VARCHAR(500) | sí | |
| logo_alt | VARCHAR(200) | no | |
| website_url | VARCHAR(500) | sí | solo `https://` |
| logo_consent_at | DATETIME(6) | sí | **no se publica sin autorización de uso de marca** |
| sort_order / is_published / deleted_at | | | |

Regla de negocio: la API pública solo devuelve empresas con `is_published = 1` **y** `logo_consent_at IS NOT NULL`.

### 4.5 `content_block` — textos editables
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id | BIGINT UNSIGNED | no | PK |
| key | VARCHAR(100) | no | `^[a-z0-9]+(\.[a-z0-9_]+)+$` (ej. `about.mission`) |
| locale | VARCHAR(10) | no | default `es-CL` |
| title | VARCHAR(200) | sí | |
| body | TEXT | no | Markdown |
| is_published | BOOL | no | |

UNIQUE (`key`, `locale`). Claves iniciales: `hero.title`, `hero.lead`, `cta.text`, `about.mission`, `about.vision`.

### 4.6 `site_setting`
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id | BIGINT UNSIGNED | no | PK |
| key | VARCHAR(100) | no | UNIQUE |
| value | TEXT | no | |
| is_public | BOOL | no | solo `is_public = 1` se expone en la API |

Claves iniciales: `company.name`, `contact.email`, `social.linkedin`. (Destinatario interno de leads va en configuración/entorno, no aquí.)

### 4.7 `legal_document` / `legal_document_version`
| Tabla | Campo | Tipo | Regla |
|---|---|---|---|
| legal_document | type | ENUM('privacy','cookies','terms','accessibility') | UNIQUE |
| | slug | VARCHAR(60) | UNIQUE (`privacidad`, `cookies`, `terminos`, `accesibilidad`) |
| | title | VARCHAR(160) | |
| legal_document_version | document_id | FK → legal_document | ON DELETE RESTRICT |
| | version | VARCHAR(20) | semver; UNIQUE (`document_id`, `version`) |
| | body | MEDIUMTEXT | Markdown |
| | published_at | DATETIME(6) | NULL = borrador |
| | is_current | BOOL | a lo más una versión vigente por documento (lo garantiza el servicio) |

Las versiones publicadas son **inmutables**: un cambio de texto = nueva versión (prueba de lo que aceptó cada titular).

### 4.8 `consent_record`
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id | BIGINT UNSIGNED | no | PK |
| legal_document_version_id | BIGINT UNSIGNED | no | FK (RESTRICT) |
| purpose | ENUM('contact','marketing','analytics_cookies') | no | |
| granted | BOOL | no | |
| subject_email_hash | BINARY(32) | sí | HMAC-SHA256(email normalizado, pepper) — permite atender derechos sin guardar email en claro aquí |
| ip_hash | BINARY(32) | sí | |
| created_at | DATETIME(6) | no | momento del consentimiento |

Append-only (no se actualiza: una revocación es un nuevo registro con `granted = 0`).

### 4.9 `contact_message` — leads (**datos personales**)
| Campo | Tipo | Nulo | Regla |
|---|---|---|---|
| id / public_id | | no | |
| name | VARCHAR(120) | no | sin saltos de línea |
| email | VARCHAR(254) | no | email válido, normalizado a minúsculas |
| company | VARCHAR(160) | sí | |
| phone | VARCHAR(32) | sí | `+` y dígitos (E.164) |
| service_id | BIGINT UNSIGNED | sí | FK → service (SET NULL) |
| message | TEXT | sí | 10–5000 caracteres; obligatorio en la API, solo queda NULL tras anonimizar |
| status | ENUM('new','read','contacted','archived','spam') | no | default `new` |
| consent_record_id | BIGINT UNSIGNED | no | FK → consent_record (RESTRICT); **sin consentimiento no hay lead** |
| ip_hash | BINARY(32) | sí | |
| user_agent | VARCHAR(255) | sí | truncado |
| retention_until | DATE | no | `created_at` + 24 meses; luego se anonimiza |
| anonymized_at | DATETIME(6) | sí | |

Índices: (`status`, `created_at`), (`email`), (`retention_until`).

### 4.10 Seguridad: `admin_user`, `role`, `admin_user_role`, `refresh_token`, `audit_log`
| Tabla | Campos clave | Regla |
|---|---|---|
| admin_user | `public_id`, `email` UNIQUE, `full_name`, `password_hash` (Argon2id), `is_active`, `mfa_secret_enc` (VARBINARY, cifrado), `failed_attempts`, `locked_until`, `last_login_at` | nunca se expone `password_hash`/`mfa_secret_enc` |
| role | `name` UNIQUE (`admin`, `editor`), `description` | |
| admin_user_role | PK (`admin_user_id`, `role_id`) | CASCADE al borrar usuario |
| refresh_token | `admin_user_id`, `token_hash` BINARY(32) UNIQUE, `expires_at`, `revoked_at`, `replaced_by_id`, `user_agent`, `ip_hash` | se guarda solo el hash; rotación en cada uso |
| audit_log | `actor_id` (SET NULL), `action`, `entity`, `entity_id`, `diff` JSON, `ip_hash`, `created_at` | append-only |

## 5. Ciclo de vida del contenido

```
borrador (is_published=0) ──publicar──▶ publicado (is_published=1) ──archivar──▶ eliminado (deleted_at)
```

## 6. Retención y derechos del titular

| Dato | Retención | Al vencer |
|---|---|---|
| `contact_message` | 24 meses (a confirmar con legal) | anonimizar: `name='[anonimizado]'`, `email` = `anon+<public_id>@invalid`, `phone/company/message/user_agent/ip_hash` = NULL, `anonymized_at = now()` |
| `consent_record` | mientras dure el tratamiento + plazo de prescripción | conservar (prueba), sin datos en claro |
| `refresh_token` | hasta `expires_at` + 30 días | borrar |
| `audit_log` | 12 meses | borrar |

Solicitudes de acceso/supresión: buscar por `email` en `contact_message` y por `subject_email_hash` en `consent_record`.

## 7. Seeds iniciales

`python -m app.seeds` (idempotente, se ejecuta con el job `migrate`) carga el contenido actual de la landing:
- 4 categorías y 10 servicios (Automatización de procesos … Soporte continuo), publicados.
- 3 banners placeholder (no publicados hasta tener imágenes reales).
- Bloques `hero.*`, `cta.text`, `about.mission`, `about.vision` (misión/visión con texto provisional, no publicados).
- 4 documentos legales con versión `0.1.0` en borrador; la de privacidad queda vigente como provisional para que el formulario funcione en dev.
- Roles `admin` y `editor`.

Los seeds **no sobrescriben** registros existentes (upsert por `slug`/`key`): una vez en producción, el contenido se edita desde el admin.
