# 02 — Seguridad

## Objetivo
Proteger el sitio contra ataques comunes (OWASP Top 10), abuso del formulario, inyección SQL, malware y manejo inseguro de peticiones. Referencias: **OWASP Top 10**, **OWASP ASVS nivel 2**, OWASP Cheat Sheets.

## Modelo de amenazas (resumen)

| Activo | Amenaza | Control principal |
|---|---|---|
| Formulario de contacto | Spam, bots, flooding, inyección de cabeceras de correo | Captcha + honeypot + rate limit + validación estricta |
| Base de datos | SQL injection, exfiltración | ORM parametrizado, mínimo privilegio, red interna |
| Panel admin | Fuerza bruta, robo de sesión, CSRF | Argon2id, lockout, MFA, cookies `SameSite=Strict`, CSRF token |
| Frontend | XSS, clickjacking, supply chain | CSP estricta, sin HTML inyectado, dependencias auditadas |
| Infraestructura | Contenedores comprometidos, secretos filtrados | No-root, imágenes escaneadas, secretos fuera de git |
| Archivos subidos (logos/banners) | Malware, archivos polimórficos | Validación de tipo real, re-encode, ClamAV, almacenamiento fuera del webroot |

## Controles por capa

### 1. Inyección SQL y datos
- **Solo SQLAlchemy** con parámetros ligados; prohibido `text()` con f-strings/concatenación (regla `ruff` S608 + revisión de código).
- Validación de entrada con Pydantic (`extra="forbid"`, longitudes máximas, tipos estrictos, enums).
- Usuario MySQL de la app sin privilegios DDL; `sql_mode` estricto.
- Datos personales: IP hasheada con *pepper*, TLS en tránsito, cifrado en reposo del volumen/backup.

### 2. Manejo de peticiones
- **Rate limiting** en dos niveles: proxy (por IP global) + aplicación (`slowapi`, por endpoint: contacto 5/h, login 5/15 min).
- Límite de tamaño de cuerpo (ej. 64 KB en JSON, configurable para uploads).
- Timeouts en proxy y en llamadas salientes (captcha, SMTP).
- CORS: en prod mismo origen (sin CORS); en dev lista explícita, nunca `*` con credenciales.
- `TrustedHostMiddleware` con hosts permitidos; `X-Forwarded-*` solo desde el proxy.
- Métodos HTTP restringidos por ruta; respuestas de error genéricas (Problem Details) sin detalles internos.
- Protección CSRF para endpoints admin con cookie (doble envío de token o `SameSite=Strict` + verificación de `Origin`).

### 3. Anti-bot / anti-spam
- **Cloudflare Turnstile** (o hCaptcha) verificado en el servidor.
- Campo honeypot oculto + tiempo mínimo de llenado.
- Normalizar y escapar contenido antes de enviarlo por correo; rechazar `\r\n` en campos que van a cabeceras.

### 4. Cabeceras HTTP de seguridad (en el proxy)
```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self' https://challenges.cloudflare.com;
  frame-src https://challenges.cloudflare.com; img-src 'self' data:; style-src 'self';
  connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Opener-Policy: same-origin
```
Ocultar `Server`/versiones. Self-host de Bootstrap y fuentes para no ampliar la CSP.

### 5. Autenticación y sesiones (admin)
- Argon2id, política de contraseñas NIST 800-63B (longitud ≥ 12, chequeo contra contraseñas filtradas).
- Lockout progresivo, MFA TOTP, refresh tokens rotativos y revocables, logout invalida servidor.
- Panel admin bajo ruta no indexada (`noindex`) y opcionalmente restringido por IP/VPN.

### 6. Malware y archivos
- Uploads solo para admins; lista blanca de tipos (PNG, JPG, WebP, SVG **sanitizado** o prohibido).
- Verificar *magic bytes*, re-encodear imágenes con Pillow (elimina payloads y EXIF), renombrar con UUID.
- Escaneo con **ClamAV** (contenedor `clamav`) antes de aceptar.
- Servir desde ruta estática sin ejecución y con `Content-Disposition` adecuado.

### 7. Supply chain y dependencias
- Lockfiles (`uv.lock`, `package-lock.json`), **Dependabot/Renovate**.
- CI: `pip-audit`, `npm audit --audit-level=high`, **Trivy** (imágenes), **hadolint**, **gitleaks** (secretos), **Bandit/ruff-S**, **Semgrep** (SAST).
- Sin scripts de CDN de terceros salvo captcha; si se usan, con SRI.

### 8. Infraestructura
- TLS 1.2+ (Caddy automático), redirección HTTP→HTTPS.
- Contenedores no-root, `no-new-privileges`, `cap_drop: ALL`, `read_only`.
- MySQL sin puerto público; firewall del host solo 80/443 (+ SSH con llave).
- Backups cifrados y probados; logs de seguridad centralizados.
- Opcional: Cloudflare delante (WAF, DDoS, bot management).

### 9. Monitoreo y respuesta
- Logs de intentos de login, rate-limit excedido, errores 5xx, con alertas.
- Plan de respuesta a incidentes y de notificación de brechas (requerido por la Ley 21.719, ver 03).
- Escaneo **OWASP ZAP** baseline en CI contra el entorno de staging.

## Entregables
- `docs/security.md` (modelo de amenazas + checklist ASVS aplicada).
- Configuración de proxy con cabeceras, middlewares FastAPI, pipeline de CI con escáneres.

## Criterios de aceptación
- [ ] OWASP ZAP baseline sin alertas *high/medium*.
- [ ] securityheaders.com nota A; SSL Labs nota A.
- [ ] Pruebas automatizadas de SQLi/XSS en el formulario (payloads comunes rechazados o neutralizados).
- [ ] Rate limits verificados con test de carga ligero.
- [ ] 0 secretos en el repo (gitleaks).
