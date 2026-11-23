import { pageMeta } from "~/lib/seo";

import type { Route } from "./+types/not-found";

// Ruta comodín: se sirve desde el SPA fallback (Nginx responde 404 para rutas desconocidas).
export const meta: Route.MetaFunction = () =>
  pageMeta({ title: "Página no encontrada", description: "", path: "/404", noindex: true });

export default function NotFound() {
  return (
    <div className="container py-5 text-center">
      <h1 className="display-6 fw-bold text-brand">Página no encontrada</h1>
      <p className="text-secondary">La página que buscas no existe o fue movida.</p>
      <a className="btn btn-brand" href="/">
        Volver al inicio
      </a>
    </div>
  );
}
