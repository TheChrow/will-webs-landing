# 03 — Aplicar políticas web

## Objetivo
Publicar e implementar las políticas legales y de buenas prácticas del sitio, conformes a la normativa chilena y estándares internacionales.

> ⚠️ Este documento es una guía técnica, no asesoría legal. Los textos finales deben ser revisados por un abogado.

## Marco normativo a considerar (Chile)
- **Ley 19.628** sobre protección de la vida privada (vigente).
- **Ley 21.719** (nueva ley de protección de datos personales, publicada en diciembre de 2024): entra en vigencia en **diciembre de 2026** — es decir, aplica prácticamente desde el lanzamiento. Introduce bases de licitud, derechos ARCO + portabilidad, deber de informar, notificación de brechas, la Agencia de Protección de Datos Personales y multas relevantes. *Verificar fecha exacta y reglamentos con asesoría legal.*
- **Ley 19.496** de protección de los derechos de los consumidores (si se ofrecen servicios/comercio en línea).
- **Ley 19.799** sobre documentos y firma electrónica (si aplica a aceptación de términos).
- Si hay visitantes/clientes de la UE: considerar **GDPR**.

## Políticas a publicar

| Documento | Ruta | Contenido mínimo |
|---|---|---|
| **Política de Privacidad** | `/privacidad` | Responsable (razón social, RUT, domicilio, contacto), datos recolectados (formulario, logs), finalidad, base de licitud (consentimiento / interés legítimo), plazos de retención, encargados (hosting, correo, captcha, analítica), transferencias internacionales, derechos del titular y cómo ejercerlos, medidas de seguridad, fecha y versión |
| **Política de Cookies** | `/cookies` | Tabla de cookies (nombre, proveedor, finalidad, duración, tipo), cómo cambiar preferencias |
| **Términos y Condiciones** | `/terminos` | Uso del sitio, propiedad intelectual, limitación de responsabilidad, ley aplicable y jurisdicción (Chile) |
| **Declaración de Accesibilidad** | `/accesibilidad` | Nivel objetivo (WCAG 2.2 AA), limitaciones conocidas, canal de contacto |
| `security.txt` | `/.well-known/security.txt` | Contacto para reporte responsable de vulnerabilidades (RFC 9116) |

Los textos se almacenan versionados en `legal_document_version` (ver 04) y se sirven desde la API.

## Implementación técnica

### Consentimiento y formulario
- Checkbox **no pre-marcado** "He leído y acepto la Política de Privacidad" (enlace) — obligatorio para enviar.
- Checkbox separado y opcional para comunicaciones comerciales.
- Se guarda `consent_record` con versión exacta de la política, fecha, finalidad (prueba del consentimiento).
- Texto informativo breve junto al formulario (quién trata los datos y para qué).

### Cookies
- Estrategia recomendada: **sin cookies no esenciales** (analítica sin cookies como Plausible/Umami) → solo aviso informativo.
- Si se usa Google Analytics u otras: **banner de consentimiento** con "Aceptar" / "Rechazar" igual de visibles y "Configurar"; nada se carga antes del consentimiento; preferencia revocable desde el footer.

### Derechos del titular
- Canal (email dedicado, ej. `privacidad@dominio`) + procedimiento interno para acceso, rectificación, supresión, oposición y portabilidad, con plazos de respuesta.
- Funciones admin para exportar y anonimizar los datos de un titular.

### Retención
- Job programado que anonimiza/elimina `contact_message` vencidos según `retention_until`.

### Otras políticas de buenas prácticas
- **Accesibilidad**: WCAG 2.2 AA (ver 01).
- **SEO/indexación**: `robots.txt`, `sitemap.xml`, `noindex` en admin y páginas de agradecimiento.
- **Divulgación responsable** de vulnerabilidades (`security.txt`).
- **Uso de marcas de clientes**: autorización escrita antes de publicar logos.
- **Registro de actividades de tratamiento** e inventario de encargados (interno).
- **Protocolo de notificación de brechas** (alineado con 02 §9).

## Entregables
- Borradores de las 4 políticas en `docs/legal/` para revisión legal.
- Páginas legales en el frontend, enlaces en footer y formulario.
- Consentimiento versionado implementado en backend.
- (Si aplica) banner de cookies con bloqueo previo de scripts.

## Criterios de aceptación
- [ ] Políticas revisadas por asesoría legal y publicadas.
- [ ] Ningún script/cookie no esencial antes del consentimiento (verificado en DevTools).
- [ ] Cada lead tiene un `consent_record` asociado a una versión de política.
- [ ] Procedimiento de derechos del titular documentado y probado.
