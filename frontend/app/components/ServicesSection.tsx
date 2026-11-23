import { useMemo, useState } from "react";

import type { Service } from "~/lib/api";
import { useServices } from "~/lib/queries";

import { ServiceIcon } from "./ServiceIcon";

export function ServicesGrid({ services }: { services: Service[] }) {
  const [filter, setFilter] = useState<string | null>(null);

  const categories = useMemo(() => {
    const seen = new Map<string, string>();
    for (const s of services) if (s.category) seen.set(s.category.slug, s.category.name);
    return [...seen.entries()].map(([slug, name]) => ({ slug, name }));
  }, [services]);

  const visible = filter ? services.filter((s) => s.category?.slug === filter) : services;

  return (
    <>
      {categories.length > 1 && (
        <div className="d-flex flex-wrap justify-content-center gap-2 mb-4" role="group" aria-label="Filtrar por categoría">
          <button
            type="button"
            className="btn btn-sm btn-outline-secondary rounded-pill filter-chip"
            aria-pressed={filter === null}
            onClick={() => setFilter(null)}
          >
            Todos
          </button>
          {categories.map((c) => (
            <button
              key={c.slug}
              type="button"
              className="btn btn-sm btn-outline-secondary rounded-pill filter-chip"
              aria-pressed={filter === c.slug}
              onClick={() => setFilter(c.slug)}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}
      <ul className="row g-4 list-unstyled mb-0" aria-live="polite">
        {visible.map((s) => (
          <li key={s.id} className="col-sm-6 col-lg-4 col-xl-3">
            <article className="card h-100 service-card shadow-sm border-0">
              <div className="card-body p-4">
                <ServiceIcon name={s.icon} />
                <h3 className="h6 fw-bold text-brand mb-2">{s.title}</h3>
                <p className="text-secondary mb-0 small">{s.summary}</p>
              </div>
            </article>
          </li>
        ))}
      </ul>
    </>
  );
}

export function ServicesSection() {
  const { data: services } = useServices();
  return (
    <section className="py-5" id="servicios" aria-labelledby="servicios-title">
      <div className="container py-4">
        <h2 id="servicios-title" className="text-center fw-bold mb-2 text-brand">
          Servicios Digitales
        </h2>
        <p className="text-center text-secondary mb-4">
          Todo lo que tu empresa necesita para operar en digital, con un solo equipo.
        </p>
        <ServicesGrid services={services ?? []} />
      </div>
    </section>
  );
}
