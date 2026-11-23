import { CircleCheck } from "lucide-react";
import { useState } from "react";

import type { Banner } from "~/lib/api";
import { useBanners, useContent } from "~/lib/queries";

const HIGHLIGHTS = [
  "Procesos automatizados de punta a punta",
  "Software a medida que crece con tu empresa",
  "Plataformas integradas e inteligencia artificial aplicada",
];

/** Carrusel accesible: sin auto-rotación (WCAG 2.2.2), controles con nombre, región anunciada. */
function BannerCarousel({ banners }: { banners: Banner[] }) {
  const [index, setIndex] = useState(0);
  const banner = banners[index];
  const go = (delta: number) => setIndex((i) => (i + delta + banners.length) % banners.length);

  return (
    <section
      className="hero-panel overflow-hidden"
      aria-roledescription="carrusel"
      aria-label="Destacados"
    >
      <div
        className="hero-carousel position-relative"
        aria-live="polite"
        aria-roledescription="diapositiva"
        aria-label={`${index + 1} de ${banners.length}`}
      >
        {banner.image_url ? (
          <img src={banner.image_url} alt={banner.image_alt} />
        ) : (
          <div className="h-100 d-flex align-items-center justify-content-center p-4 text-center">
            <p className="h4 mb-0">{banner.title}</p>
          </div>
        )}
      </div>
      {banners.length > 1 && (
        <div className="d-flex justify-content-between align-items-center p-3">
          <button type="button" className="btn btn-outline-light btn-sm" onClick={() => go(-1)}>
            Anterior
          </button>
          <span className="small">
            {index + 1} / {banners.length}
          </span>
          <button type="button" className="btn btn-outline-light btn-sm" onClick={() => go(1)}>
            Siguiente
          </button>
        </div>
      )}
    </section>
  );
}

export function Hero() {
  const { data: content } = useContent();
  const { data: banners } = useBanners();

  return (
    <section className="hero text-white" id="inicio" aria-labelledby="hero-title">
      <div className="container py-5">
        <div className="row align-items-center g-5 py-lg-4">
          <div className="col-lg-6">
            <h1 id="hero-title" className="display-5 fw-bold mb-3">
              {content?.["hero.title"]?.body}
            </h1>
            <p className="lead hero-lead mb-4">{content?.["hero.lead"]?.body}</p>
            <div className="d-flex flex-wrap gap-3">
              <a href="#contacto" className="btn btn-brand btn-lg">
                Agenda una conversación
              </a>
              <a href="#servicios" className="btn btn-outline-light btn-lg">
                Ver servicios
              </a>
            </div>
          </div>
          <div className="col-lg-6">
            {banners && banners.length > 0 ? (
              <BannerCarousel banners={banners} />
            ) : (
              <div className="hero-panel p-4 p-lg-5">
                <p className="text-uppercase small fw-semibold text-brand-accent mb-3">
                  Lo que logramos contigo
                </p>
                <ul className="list-unstyled mb-0">
                  {HIGHLIGHTS.map((item) => (
                    <li key={item} className="d-flex gap-3 align-items-start">
                      <CircleCheck className="flex-shrink-0 text-brand-accent" aria-hidden="true" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
