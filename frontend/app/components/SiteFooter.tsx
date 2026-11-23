import { Link } from "react-router";

import { useSettings } from "~/lib/queries";

import { Brand } from "./SiteHeader";

const LEGAL = [
  { to: "/privacidad", label: "Privacidad" },
  { to: "/cookies", label: "Cookies" },
  { to: "/terminos", label: "Términos" },
  { to: "/accesibilidad", label: "Accesibilidad" },
];

export function SiteFooter() {
  const { data: settings } = useSettings();
  const email = settings?.["contact.email"];
  const company = settings?.["company.name"] ?? "Will-Webs";

  return (
    <footer className="bg-brand-dark text-white py-5">
      <div className="container">
        <div className="row g-4">
          <div className="col-md-4">
            <p className="fw-bold mb-2">
              <Brand />
            </p>
            <p className="small mb-0 opacity-75">
              Software a medida, automatización e integraciones para empresas.
            </p>
          </div>
          <nav className="col-6 col-md-4" aria-label="Sitio">
            <p className="small fw-semibold text-uppercase opacity-75 mb-2">Sitio</p>
            <ul className="list-unstyled small mb-0">
              <li><a className="link-light text-decoration-none" href="/#servicios">Servicios</a></li>
              <li><a className="link-light text-decoration-none" href="/#sobre-nosotros">Sobre nosotros</a></li>
              <li><a className="link-light text-decoration-none" href="/#contacto">Contacto</a></li>
              {email && (
                <li>
                  <a className="link-light text-decoration-none" href={`mailto:${email}`}>
                    {email}
                  </a>
                </li>
              )}
            </ul>
          </nav>
          <nav className="col-6 col-md-4" aria-label="Legal">
            <p className="small fw-semibold text-uppercase opacity-75 mb-2">Legal</p>
            <ul className="list-unstyled small mb-0">
              {LEGAL.map((l) => (
                <li key={l.to}>
                  <Link className="link-light text-decoration-none" to={l.to}>
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <hr className="border-secondary my-4" />
        <p className="small mb-0 opacity-75">
          © {new Date().getFullYear()} {company}. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}
