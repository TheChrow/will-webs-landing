import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router";

const NAV = [
  { href: "/#servicios", label: "Servicios" },
  { href: "/#sobre-nosotros", label: "Sobre nosotros" },
];

export function Brand() {
  return (
    <>
      <span className="text-brand-accent" aria-hidden="true">
        ▰
      </span>{" "}
      Will-Webs
    </>
  );
}

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  // Cerrar el menú móvil al navegar.
  useEffect(() => setOpen(false), [location.pathname, location.hash]);

  return (
    <header>
      <nav
        className="navbar navbar-expand-lg navbar-dark bg-brand-dark sticky-top shadow-sm site-navbar"
        aria-label="Principal"
      >
        <div className="container">
          <Link className="navbar-brand fw-bold" to="/">
            <Brand />
          </Link>
          <button
            className="navbar-toggler"
            type="button"
            aria-controls="mainNav"
            aria-expanded={open}
            aria-label={open ? "Cerrar menú" : "Abrir menú"}
            onClick={() => setOpen((v) => !v)}
          >
            <span className="navbar-toggler-icon" />
          </button>
          <div className={`collapse navbar-collapse${open ? " show" : ""}`} id="mainNav">
            <ul className="navbar-nav ms-auto align-items-lg-center gap-lg-2 py-2 py-lg-0">
              {NAV.map((item) => (
                <li className="nav-item" key={item.href}>
                  <a className="nav-link" href={item.href}>
                    {item.label}
                  </a>
                </li>
              ))}
              <li className="nav-item ms-lg-2 mt-2 mt-lg-0">
                <a className="btn btn-brand" href="/#contacto">
                  Contáctanos
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </header>
  );
}
