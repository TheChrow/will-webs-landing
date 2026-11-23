# Seguridad — Will-Webs Site

> 2026-11-23 · Referencias: OWASP Top 10 (2021), OWASP ASVS 4.0 nivel 2. Complementa
> [specs/001-will-webs-site/02-security.md](../specs/001-will-webs-site/02-security.md).

## 1. Modelo de amenazas y controles implementados

| Activo | Amenaza | Controles en el código |
|---|---|---|
| Formulario de contacto | Spam, bots, flooding | Honeypot + tiempo mínimo (respuesta 202 silenciosa), Turnstile verificado en servidor, rate limit 5/h por IP y por email |
| | Inyección de cabeceras de correo | Campos de una línea sin CR/LF ni controles; `EmailMessage` rechaza saltos |
| Base de datos | Inyección SQL | Solo SQLAlchemy con parámetros ligados; regla `ruff S608`; slugs/keys validados por regex; `LIKE` con `autoescape` |
| | Exfiltración / abuso de credenciales | Usuario de la app solo DML; migraciones con otro usuario; MySQL sin puerto público en prod (red `internal`) |
| Datos personales | Filtración, retención excesiva | IP/email seudonimizados (HMAC-SHA256 + pepper); retención 24 meses con anonimización automática; exportación y supresión por titular; errores 422 sin eco del valor |
| Panel admin | Fuerza bruta | Argon2id; bloqueo 15 min tras 5 fallos; rate limit 10/15 min por IP; mismo mensaje para usuario inexistente/bloqueado/clave errónea (tiempo igualado) |
| | Robo de sesión | Access JWT de 15 min solo en memoria (no `localStorage`); refresh opaco en cookie `HttpOnly; SameSite=Strict; Secure` (prod), con path restringido, rotación y detección de reutilización (revoca toda la familia) |
| | CSRF | Cookie `SameSite=Strict` + verificación de `Origin`/`Referer` en refresh/logout; el resto usa `Authorization: Bearer` |
| | Escalada de privilegios | RBAC por endpoint (`admin` / `editor`); legal, auditoría y derechos del titular solo `admin` |
| | Manipulación de JWT | Algoritmo fijo HS256 (rechaza `none`), `aud`/`iss`/`exp` obligatorios, tipo `access` |
| Contenido | XSS almacenado | React escapa todo; Markdown legal con `react-markdown` + `skipHtml`; enlaces de banners solo `#`, `/ruta` o `https://` |
| | XSS reflejado / inyección de scripts | CSP sin `'unsafe-inline'` (hashes calculados en el build), `object-src 'none'`, `base-uri 'self'` |
| Navegador | Clickjacking, sniffing | `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `COOP`, HSTS (prod) |
| Trazabilidad | Repudio | Audit log append-only de toda escritura admin, login y fallos (actor, diff, IP seudonimizada) |
| Infraestructura | Contenedor comprometido | Usuarios no-root numéricos, `read_only`, `cap_drop: ALL`, `no-new-privileges`, límites de memoria/CPU |
| | Secretos | `.env` y `secrets/` fuera de git; Docker secrets en prod; la API no arranca en prod sin `hash_pepper`, `turnstile_secret_key` y `jwt_secret` |
| | Exposición de información | Swagger/OpenAPI desactivados en prod; `Server` oculto; `server_tokens off`; `Cache-Control: no-store` en `/api/v1/admin` |

## 2. Checklist ASVS (nivel 2) — estado

| Área ASVS | Estado | Nota |
|---|---|---|
| V2 Autenticación | ✅ parcial | Falta **MFA (TOTP)** para admins y verificación de contraseñas filtradas (HIBP) |
| V3 Sesiones | ✅ | Rotación, revocación, expiración, cookie endurecida |
| V4 Control de acceso | ✅ | RBAC servidor; IDs públicos ULID (no enumerables) |
| V5 Validación / codificación | ✅ | Pydantic estricto (`extra="forbid"`), Zod en cliente |
| V7 Errores y logs | ✅ | Problem Details sin stack; `X-Request-ID`; sin datos personales en logs |
| V8 Protección de datos | ✅ | Seudonimización, retención, derechos del titular |
| V9 Comunicaciones | ✅ prod | TLS automático (Caddy), HSTS preload |
| V12 Archivos | ⏳ | Aún no hay subida de archivos (logos/banners por URL). Al implementarla: verificación de *magic bytes*, re-encode y ClamAV |
| V13 API | ✅ | Métodos explícitos, límites de paginación, límite de body 1 MB en el proxy |
| V14 Configuración | ✅ | Hardening de contenedores, dependencias fijadas, escaneos |

## 3. Resultados de escaneo (2026-11-23)

| Herramienta | Alcance | Resultado |
|---|---|---|
| `pip-audit` | dependencias Python de producción | 0 vulnerabilidades conocidas |
| `npm audit --omit=dev` | dependencias del frontend | 0 vulnerabilidades |
| `hadolint` | `backend/Dockerfile`, `frontend/Dockerfile` | sin hallazgos |
| `gitleaks` | historial de git + código | sin secretos (hay falsos positivos marcados en tests) |
| `ruff` (incluye reglas Bandit `S`) | backend | sin hallazgos |
| `trivy` HIGH/CRITICAL con corrección disponible | imagen backend | 0 |
| | imagen frontend | 6, todas del paquete `nginx` de la imagen base (ver riesgos aceptados) |
| | `caddy:2.11-alpine` | 1 HIGH (`golang.org/x/net/html`) |
| | `mysql:8.4` | 57 HIGH en paquetes del SO (curl, krb5, util-linux…) |

Las imágenes propias aplican `apt-get upgrade` / `apk upgrade` en el build porque las bases oficiales
suelen ir atrasadas con los parches.

## 4. Riesgos aceptados (temporales)

| Riesgo | Por qué se acepta | Acción |
|---|---|---|
| nginx 1.30.6 — CVE crítico en el módulo **mail** | El módulo de proxy de correo no se usa (solo HTTP estático); la versión corregida 1.30.7 aún no está en la imagen `nginx-unprivileged` | Reconstruir con `--pull` cuando se publique; CI lo detecta |
| Paquetes del SO en `mysql:8.4` | MySQL no tiene puerto publicado ni salida a Internet en prod (red `internal`); los paquetes afectados (curl, krb5…) no se usan en la ruta de datos | Actualizar la imagen con `docker compose pull` en cada mantenimiento |
| `golang.org/x/net/html` en Caddy | Caddy no parsea HTML en esta configuración (sin `templates`) | Actualizar a la siguiente 2.11.x |
| Rate limit en memoria por proceso | Con N workers el límite efectivo es ≤ N veces el configurado | Rate limit en el proxy (plugin `caddy-ratelimit`) o Redis antes de escalar horizontalmente |

## 5. Pendientes (antes de producción o en la siguiente iteración)

- [ ] MFA TOTP obligatorio para el rol `admin`.
- [ ] Rate limiting en el proxy (Caddy con `caddy-ratelimit`) o WAF (Cloudflare) delante.
- [ ] OWASP ZAP baseline contra staging en CI.
- [ ] Backups cifrados de MySQL con prueba de restauración.
- [ ] Alertas sobre `login_failed`, `refresh_reuse_detected` y picos de 429/5xx.
- [ ] `security.txt` (RFC 9116) cuando exista el email de seguridad.
- [ ] Programar el job de retención (`python -m app.jobs.retention`) a diario.
