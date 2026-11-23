# Auditoría UX/UI — landing → sitio React

> 2026-11-23 · Alcance: landing estática Bootstrap 5 (commit `a0b9d34`) frente al frontend React de la Fase 2.
> Método: revisión heurística (Nielsen), WCAG 2.2 AA, revisión de rendimiento/seguridad del HTML.

## Hallazgos y resolución

| # | Área | Hallazgo en la landing | Severidad | Resolución en Fase 2 |
|---|---|---|---|---|
| 1 | Hero | Carrusel con auto-rotación sin pausa (WCAG 2.2.2) y slides vacíos ("Banner 1/2/3") | Alta | Sin auto-play. Si hay banners publicados en la API: carrusel con controles con nombre y región `aria-live`. Si no: panel de beneficios |
| 2 | CTA | Dos CTA idénticos "Contáctenos" | Media | Primario "Agenda una conversación", secundario "Ver servicios"; banda CTA "Escríbenos" |
| 3 | Servicios | 10 tarjetas solo texto, difíciles de escanear | Media | Íconos por servicio, categorías con filtro (`aria-pressed`), datos desde la API |
| 4 | Sobre nosotros | Misión/Visión vacías | Alta | Se muestran cuando están publicadas en la API; mientras tanto, propuesta de valor (3 pilares) |
| 5 | Cinta de empresas | Ciclo de 3.6 s (ilegible), logos placeholder, sin control de movimiento | Media | 30 s por ciclo, pausa al pasar el mouse/foco, `prefers-reduced-motion`, copia oculta a lectores de pantalla; solo se muestra con empresas autorizadas |
| 6 | Formulario | `action="#"`, sin validación accesible, sin feedback, sin consentimiento | Crítica | React Hook Form + Zod (espejo del backend), errores con `aria-invalid`/`aria-describedby`, estado `aria-live`, consentimiento obligatorio + opt-in comercial separado, honeypot, Turnstile opcional |
| 7 | Footer | Sin enlaces legales ni contacto | Alta | Navegación del sitio, email de contacto (API), enlaces a las 4 páginas legales |
| 8 | SEO | Sin Open Graph, datos estructurados ni canonical | Media | Meta por ruta, OG, JSON-LD `Organization`, canonical con `VITE_SITE_URL`, `robots.txt`, HTML pre-renderizado |
| 9 | Rendimiento | Bootstrap completo (CSS + JS) desde CDN | Media | Bootstrap SCSS self-hosted con solo los módulos usados; sin JS de Bootstrap (navbar en React); assets con hash e `immutable` |
| 10 | Seguridad | CSP debía permitir el CDN | Media | CSP estricta sin `'unsafe-inline'`: hashes de los scripts inline calculados en el build |
| 11 | Accesibilidad | Sin skip link, foco poco visible, menú dependiente de JS de Bootstrap | Media | Skip link, `:focus-visible` de alto contraste, `aria-expanded` en el menú, landmarks y encabezados jerárquicos |
| 12 | Errores | Sin página 404 | Baja | 404 real (estado HTTP 404) con página propia |

## Pendiente (requiere contenido o decisión de negocio)

- Textos reales de Misión/Visión y publicación desde el admin.
- Imágenes reales del hero (si se mantiene carrusel) y logos de clientes con autorización.
- Casos de éxito / testimonios (prueba social).
- Dominio definitivo para `VITE_SITE_URL` y `sitemap.xml`.
- Prueba con 3–5 usuarios objetivo y auditoría Lighthouse/axe automatizada en CI (Fase 4).
