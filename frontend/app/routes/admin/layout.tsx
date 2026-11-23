import { NavLink, Outlet } from "react-router";

import { AuthProvider, useAuth } from "~/admin/auth";
import { LoginForm } from "~/admin/LoginForm";
import { pageMeta } from "~/lib/seo";

import type { Route } from "./+types/layout";

export const meta: Route.MetaFunction = () =>
  pageMeta({ title: "Panel", description: "Panel de administración", path: "/admin", noindex: true });

const NAV = [
  { to: "/admin", label: "Leads", end: true },
  { to: "/admin/servicios", label: "Servicios" },
  { to: "/admin/contenido", label: "Contenido" },
  { to: "/admin/legal", label: "Legal", role: "admin" },
  { to: "/admin/auditoria", label: "Auditoría", role: "admin" },
];

function Shell() {
  const { state, logout, hasRole } = useAuth();

  if (state.status === "loading") {
    return (
      <main className="admin-shell d-flex align-items-center justify-content-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Cargando…</span>
        </div>
      </main>
    );
  }
  if (state.status === "anonymous") return <LoginForm notice={state.reason} />;

  return (
    <div className="admin-shell d-flex flex-column flex-md-row">
      <nav className="admin-sidebar p-3 flex-shrink-0" aria-label="Panel">
        <p className="text-white fw-bold mb-3">
          <span className="text-brand-accent" aria-hidden="true">▰</span> Panel
        </p>
        <ul className="nav nav-pills flex-md-column gap-1">
          {NAV.filter((n) => !n.role || hasRole(n.role)).map((n) => (
            <li className="nav-item" key={n.to}>
              <NavLink to={n.to} end={n.end} className="nav-link">
                {n.label}
              </NavLink>
            </li>
          ))}
        </ul>
        <hr className="border-secondary" />
        <p className="small text-white-50 mb-2 text-break">{state.user.email}</p>
        <button type="button" className="btn btn-sm btn-outline-light" onClick={logout}>
          Cerrar sesión
        </button>
      </nav>
      <main className="flex-grow-1 p-3 p-lg-4 overflow-auto" id="contenido">
        <Outlet />
      </main>
    </div>
  );
}

export default function AdminLayout() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
