# Will-Webs — Landing (will-webs-landing)

Landing de **una sola página** (one-page) construida con **Bootstrap 5** (vía CDN),
generada a partir del plano de Excalidraw. Navegación por anclas.

## Cómo verlo
Abre `index.html` en el navegador (no requiere build; Bootstrap se carga desde CDN).

## Paleta de marca
| Color | Hex | Uso |
|---|---|---|
| Azul marino oscuro | `#09274F` | Fondos oscuros (navbar, hero, footer) — `.bg-brand-dark` |
| Azul medio | `#094183` | Títulos y acentos — `.text-brand`, `.bg-brand` |
| Azul vivo | `#014DBF` | Primario / CTA (`--bs-primary`) — `.btn-brand`, `.text-brand-accent` |

Definidos como variables en `styles.css` (`:root`), sobrescribiendo el `primary` de Bootstrap.

## Mapa: plano → componente

| Sección del plano | Componente Bootstrap | Notas |
|---|---|---|
| Header (Logo, menú, botón Contactos) | `navbar navbar-expand-lg` | Menú hamburguesa móvil incluido; botón **Contactos** → `#contacto` |
| Banner / Slider | `carousel` (`#heroCarousel`) | Carrusel de 3 slides con indicadores y auto-rotación (JS de Bootstrap) |
| Servicios Digitales ("Listados") | grid de `card` (`.row > .col`) | 10 servicios del listado del plano |
| Botón Contáctenos | banda CTA (`.bg-brand`) | CTA intermedio que redirige al formulario |
| Misión y Visión / Sobre nosotros | 2 `card` | Misión y Visión |
| Empresas — cinta automática (3.6 s) | `.marquee` (CSS propio) | Ciclo controlado con `--marquee-duration: 3.6s` |
| Formulario de Contacto | `form` de Bootstrap | Destino del menú "Contactos" y del CTA |
| Footer | `footer .bg-brand-dark` | Logo, enlaces y copyright |

## Pendientes / decisiones
- **Marquesina**: la animación recorre `-50%` asumiendo el set de logos **duplicado**
  en el HTML. Si cambias la cantidad de logos, mantén la copia para el loop sin saltos.
- **Formulario**: el `action` está vacío; conectar al backend/servicio de correo.
- **Contenido real**: textos de Misión/Visión, imágenes del slider y logos de empresas.
- **(Opcional)** Servir Bootstrap localmente (npm) en vez de CDN para producción offline.

## Archivos
- `index.html` — estructura y contenido (clases de Bootstrap)
- `styles.css` — overrides de marca sobre Bootstrap + marquesina
