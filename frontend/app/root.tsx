import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLocation,
} from "react-router";

import type { Route } from "./+types/root";
import { SiteFooter } from "./components/SiteFooter";
import { SiteHeader } from "./components/SiteHeader";
import { createQueryClient } from "./lib/queries";
import "./styles/main.scss";

export const links: Route.LinksFunction = () => [
  { rel: "icon", href: "/favicon.svg", type: "image/svg+xml" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-CL">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#09274F" />
        <Meta />
        <Links />
      </head>
      <body>
        <a className="skip-link" href="#contenido">
          Saltar al contenido
        </a>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  const [queryClient] = useState(createQueryClient);
  const isAdmin = useLocation().pathname.startsWith("/admin");
  if (isAdmin) {
    // El panel tiene su propio layout (sin cabecera ni pie del sitio público).
    return (
      <QueryClientProvider client={queryClient}>
        <Outlet />
      </QueryClientProvider>
    );
  }
  return (
    <QueryClientProvider client={queryClient}>
      <SiteHeader />
      <main id="contenido" tabIndex={-1}>
        <Outlet />
      </main>
      <SiteFooter />
    </QueryClientProvider>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  const notFound = isRouteErrorResponse(error) && error.status === 404;
  return (
    <main id="contenido" className="container py-5 text-center">
      <h1 className="display-6 fw-bold text-brand">
        {notFound ? "Página no encontrada" : "Algo salió mal"}
      </h1>
      <p className="text-secondary">
        {notFound
          ? "La página que buscas no existe o fue movida."
          : "Ocurrió un error inesperado. Intenta recargar la página."}
      </p>
      <a className="btn btn-brand" href="/">
        Volver al inicio
      </a>
    </main>
  );
}
