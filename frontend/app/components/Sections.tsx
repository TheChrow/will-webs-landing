import { useClients, useContent } from "~/lib/queries";

export function CtaBand() {
  const { data: content } = useContent();
  return (
    <section className="py-5 bg-brand text-white" aria-label="Llamado a la acción">
      <div className="container">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3">
          <p className="h4 mb-0">{content?.["cta.text"]?.body}</p>
          <a href="#contacto" className="btn btn-light btn-lg text-brand fw-semibold">
            Escríbenos
          </a>
        </div>
      </div>
    </section>
  );
}

// Propuesta de valor mientras Misión/Visión no estén publicadas en la API.
const VALUES = [
  { key: "value.team", title: "Un solo equipo", body: "Desarrollo, infraestructura e IA coordinados por un mismo equipo, con un único punto de contacto." },
  { key: "value.security", title: "Seguridad desde el diseño", body: "Buenas prácticas de seguridad y protección de datos en cada proyecto, no como un agregado." },
  { key: "value.support", title: "Acompañamiento continuo", body: "Te acompañamos después de la entrega con soporte, mejoras y evolución de tus sistemas." },
];

/** Misión y Visión desde la API; si no están publicadas, la propuesta de valor. */
export function AboutSection() {
  const { data: content } = useContent();
  const published = ["about.mission", "about.vision"]
    .map((key) => content?.[key])
    .filter((b) => b !== undefined);
  const blocks = published.length > 0 ? published : VALUES;
  const col = blocks.length === 3 ? "col-md-4" : "col-md-6";

  return (
    <section className="py-5" id="sobre-nosotros" aria-labelledby="about-title">
      <div className="container py-4">
        <h2 id="about-title" className="text-center fw-bold mb-5 text-brand">
          Sobre nosotros
        </h2>
        <div className="row g-4">
          {blocks.map((b) => (
            <div className={col} key={b.key}>
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <h3 className="h4 fw-bold text-brand mb-3">{b.title}</h3>
                  <p className="text-secondary mb-0">{b.body}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/** Cinta de logos: se oculta si no hay empresas con autorización publicada. */
export function ClientsMarquee() {
  const { data: clients } = useClients();
  if (!clients || clients.length === 0) return null;

  const renderItem = (hidden: boolean) =>
    clients.map((c) => (
      <li className="marquee__item" key={`${c.id}-${hidden}`} aria-hidden={hidden || undefined}>
        {c.logo_url ? <img src={c.logo_url} alt={hidden ? "" : c.logo_alt} /> : c.name}
      </li>
    ));

  return (
    <section className="py-5 bg-light" aria-labelledby="clients-title">
      <div className="container">
        <h2 id="clients-title" className="h6 text-center text-secondary text-uppercase mb-4">
          Empresas que confían en nosotros
        </h2>
        <div className="marquee">
          {/* Lista duplicada para el loop continuo; la copia se oculta a lectores de pantalla. */}
          <ul className="marquee__track list-unstyled mb-0">
            {renderItem(false)}
            {renderItem(true)}
          </ul>
        </div>
      </div>
    </section>
  );
}
