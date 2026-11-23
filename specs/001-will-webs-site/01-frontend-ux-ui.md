# 01 — Revisión Frontend, UX/UI y tecnologías React

## Objetivo
Auditar la landing actual, definir el stack React y planificar la migración con paridad visual y mejoras de UX/UI, accesibilidad, SEO y rendimiento.

## A. Auditoría de la landing actual (hallazgos iniciales)

| Área | Hallazgo | Acción propuesta |
|---|---|---|
| Hero | Carrusel con auto-rotación: mala práctica de UX/accesibilidad (WCAG 2.2.2 exige pausa), baja interacción tras el 1.er slide | Hero estático con 1 mensaje fuerte; si se mantiene el slider: botón pausa, sin auto-play o respetar `prefers-reduced-motion` |
| Servicios | 10 cards solo con texto, sin íconos ni jerarquía; difícil de escanear | Agrupar en 3–4 categorías, íconos, enlace a detalle o modal |
| CTA | Dos CTA iguales ("Contáctenos") | Diferenciar: primario "Agenda una reunión", secundario "Ver servicios" |
| Sobre nosotros | Misión/Visión vacías | Contenido real + propuesta de valor, métricas, equipo |
| Cinta empresas | Marquesina 3.6 s (rápida), logos placeholder | Ralentizar (20–40 s), pausa en hover/foco, `prefers-reduced-motion` |
| Formulario | `action="#"`, sin validación accesible ni feedback, sin consentimiento | Validación cliente + servidor, mensajes `aria-live`, checkbox de consentimiento con enlace a política |
| Prueba social | No hay testimonios ni casos | Sección de casos de éxito (v1 o v2) |
| Footer | Sin enlaces legales ni datos de contacto | Políticas, contacto, redes, RUT/razón social |
| SEO | Sin Open Graph, sin datos estructurados, sin sitemap | OG/Twitter cards, JSON-LD `Organization`/`LocalBusiness`, `sitemap.xml`, `robots.txt` |
| Rendimiento | Bootstrap completo por CDN (CSS+JS) | Importar solo módulos SCSS usados, self-host (también mejora CSP y privacidad) |

Validar con: Lighthouse, axe DevTools, prueba con teclado y lector de pantalla (NVDA), y 3–5 pruebas rápidas con usuarios objetivo.

## B. Stack recomendado

| Necesidad | Elección | Por qué |
|---|---|---|
| Base | **React 19 + TypeScript + Vite** | Estándar actual, build rápido |
| Routing + SEO | **React Router v7 (modo framework) con `prerender`** | Genera HTML estático para las páginas públicas (SEO, LCP) sin servidor Node en prod |
| Estilos | **Bootstrap 5.3 vía npm + SCSS** (con variables de marca) | Reutiliza el trabajo existente y la paleta; alternativa: Tailwind v4 si se quiere rediseño completo |
| Datos del API | **TanStack Query** | Caché, reintentos, estados de carga |
| Formularios | **React Hook Form + Zod** | Validación tipada, el schema Zod refleja el de Pydantic |
| Íconos | Lucide / Bootstrap Icons (SVG, tree-shaken) | |
| Tests | **Vitest + Testing Library**, **Playwright** (E2E + axe) | |
| Calidad | ESLint (flat config) + Prettier, `tsc --noEmit` en CI | |

Tipos del API generados desde el OpenAPI de FastAPI (`openapi-typescript`) para no duplicar contratos.

## C. Sistema de diseño
- Tokens: colores de marca (`#09274F`, `#094183`, `#014DBF`) + neutros + estados (éxito/error), verificando **contraste AA** (≥ 4.5:1 texto normal).
- Escala tipográfica, espaciado, radios, sombras como variables SCSS/CSS.
- Componentes: `Navbar`, `Hero`, `ServiceCard`, `CtaBand`, `AboutSection`, `LogoMarquee`, `ContactForm`, `Footer`, `CookieBanner`, páginas legales.
- Wireframes/mockups en Figma o Excalidraw (el plano original ya existe) antes de codificar cambios de layout.

## D. Requisitos no funcionales
- Responsive mobile-first (360 → 1440 px+).
- **Core Web Vitals**: LCP < 2.5 s, INP < 200 ms, CLS < 0.1.
- Imágenes AVIF/WebP con `srcset`, `width/height` definidos, lazy-loading bajo el fold.
- Fuentes self-hosted con `font-display: swap`.
- Accesibilidad **WCAG 2.2 AA**: foco visible, *skip link*, landmarks, `alt` obligatorio, navegación completa por teclado.
- Sin `dangerouslySetInnerHTML`; si se renderiza Markdown del CMS, sanitizar (DOMPurify).

## Plan de trabajo
1. Auditoría formal (Lighthouse + axe + heurísticas de Nielsen) → informe con prioridades.
2. Propuesta de wireframes con mejoras aprobadas.
3. Scaffold `frontend/` (Vite + RR7 + TS + SCSS) dentro de Docker.
4. Migrar secciones a componentes con datos mock (paridad visual).
5. Integrar API (TanStack Query) y formulario real.
6. Páginas legales + banner de cookies (ver 03).
7. E2E + auditoría final.

## Criterios de aceptación
- [ ] Informe de auditoría UX/UI entregado y priorizado.
- [ ] Paridad visual (o mejoras aprobadas) en todas las secciones.
- [ ] Lighthouse móvil ≥ 90 en las 4 categorías; axe sin violaciones serias.
- [ ] Contenido servido desde la API, con fallback prerenderizado.
