import type { Config } from "@react-router/dev/config";

export default {
  // Sitio estático: sin servidor Node en producción. Todas las rutas estáticas se
  // pre-renderizan a HTML en el build (SEO + LCP); Nginx sirve build/client.
  ssr: false,
  prerender: true,
} satisfies Config;
