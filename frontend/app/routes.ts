import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("privacidad", "routes/privacidad.tsx"),
  route("cookies", "routes/cookies.tsx"),
  route("terminos", "routes/terminos.tsx"),
  route("accesibilidad", "routes/accesibilidad.tsx"),
  route("*", "routes/not-found.tsx"),
] satisfies RouteConfig;
