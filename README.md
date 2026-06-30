# LED Studio — Landing (esqueleto)

Estructura HTML/CSS generada a partir del plano de Excalidraw. Sitio de **una sola página**
(one-page) con navegación por anclas.

## Cómo verlo
Abre `index.html` en el navegador (no requiere build).

## Mapa: plano → componente

| Sección del plano | Bloque en `index.html` | Notas |
|---|---|---|
| Header (Logo, menú, botón Contactos) | `<header class="site-header">` | Nav fija; el botón **Contactos** apunta a `#contacto` (el "Redirige" del plano) |
| Banner / Slider | `<section class="hero">` → `.hero__slider` | Hero con titular + CTA y carrusel de 3 slides (lógica de JS pendiente) |
| Servicios Digitales ("Listados") | `<section class="services">` | Grid con los 10 servicios del listado del plano |
| Botón Contáctenos | `<section class="cta-band">` | CTA intermedio que redirige al formulario |
| Misión y Visión / Sobre nosotros | `<section class="about">` | Dos tarjetas: Misión y Visión |
| Empresas — cinta automática (3.6 s) | `<section class="clients">` → `.marquee` | Marquesina CSS; el ciclo se controla con `--marquee-duration: 3.6s` |
| Formulario de Contacto | `<section class="contact">` | Destino del menú "Contactos" y del CTA |
| Footer | `<footer class="site-footer">` | Logo, enlaces y copyright |

## Pendientes / decisiones
- **Slider del hero**: falta el JS de auto-rotación e indicadores (o usar una librería).
- **Menú móvil**: en <820px el nav se oculta; falta el botón hamburguesa.
- **Marquesina**: la animación recorre `-50%` asumiendo el set de logos **duplicado**
  en el HTML. Si cambias la cantidad de logos, mantén la copia para el loop sin saltos.
- **Formulario**: el `action` está vacío; conectar al backend/servicio de correo.
- **Contenido real**: textos de Misión/Visión, imágenes del slider y logos de empresas.
- **"Sobre nosotros"**: en el plano aparece como "Sobrenostros" — usar el texto correcto.

## Archivos
- `index.html` — estructura y contenido
- `styles.css` — estilos y tokens de diseño (variables CSS)
