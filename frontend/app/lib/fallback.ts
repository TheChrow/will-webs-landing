/**
 * Contenido de respaldo = seeds de la API (backend/app/seeds.py).
 * Se usa para el HTML pre-renderizado (SEO, primer pintado) y si la API no responde.
 * La API es la fuente de verdad: al cargar, el cliente reemplaza esto por los datos reales.
 */
import type { ContentBlock, Service } from "./api";

const cat = (slug: string, name: string) => ({ slug, name });
const DEV = cat("desarrollo", "Desarrollo de software");
const IA = cat("automatizacion-ia", "Automatización e IA");
const INFRA = cat("infraestructura", "Infraestructura y seguridad");
const CONS = cat("consultoria", "Consultoría y soporte");

const svc = (
  slug: string,
  title: string,
  summary: string,
  category: Service["category"],
  icon: string,
): Service => ({ id: slug, slug, title, summary, description: null, icon, category });

export const FALLBACK_SERVICES: Service[] = [
  svc("automatizacion-de-procesos", "Automatización de procesos", "Automatizamos procesos empresariales.", IA, "workflow"),
  svc("software-a-medida", "Software a medida", "Creamos software que se adapta a tu empresa.", DEV, "code"),
  svc("integraciones", "Integraciones", "Integramos todas tus plataformas.", DEV, "plug"),
  svc("inteligencia-artificial", "Inteligencia Artificial", "Implementamos IA para aumentar la productividad.", IA, "sparkles"),
  svc("infraestructura", "Infraestructura", "Modernizamos tu infraestructura tecnológica.", INFRA, "server"),
  svc("correo-empresarial", "Correo empresarial", "Migramos y administramos tu correo empresarial.", INFRA, "mail"),
  svc("aplicaciones-web", "Aplicaciones web", "Desarrollamos aplicaciones web escalables.", DEV, "globe"),
  svc("respaldo-y-seguridad", "Respaldo y seguridad", "Protegemos y respaldamos tu información.", INFRA, "shield-check"),
  svc("transformacion-digital", "Transformación digital", "Acompañamos la transformación digital de tu empresa.", CONS, "trending-up"),
  svc("soporte-continuo", "Soporte continuo", "Brindamos soporte tecnológico continuo.", CONS, "life-buoy"),
];

const block = (key: string, body: string, title: string | null = null): ContentBlock => ({
  key,
  locale: "es-CL",
  title,
  body,
});

export const FALLBACK_CONTENT: ContentBlock[] = [
  block("hero.title", "Modernizamos tu empresa con software a medida"),
  block(
    "hero.lead",
    "Automatizamos procesos, integramos tus plataformas e implementamos inteligencia artificial para aumentar tu productividad.",
  ),
  block("cta.text", "¿Listo para dar el siguiente paso?"),
];

export const FALLBACK_SETTINGS: Record<string, string> = {
  "company.name": "Will-Webs",
};
