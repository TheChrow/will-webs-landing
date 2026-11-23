import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("privacidad", "routes/privacidad.tsx"),
  route("cookies", "routes/cookies.tsx"),
  route("terminos", "routes/terminos.tsx"),
  route("accesibilidad", "routes/accesibilidad.tsx"),
  route("admin", "routes/admin/layout.tsx", [
    index("routes/admin/leads.tsx"),
    route("servicios", "routes/admin/services.tsx"),
    route("contenido", "routes/admin/content.tsx"),
    route("legal", "routes/admin/legal.tsx"),
    route("auditoria", "routes/admin/audit.tsx"),
  ]),
  route("*", "routes/not-found.tsx"),
] satisfies RouteConfig;
