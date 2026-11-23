import { reactRouter } from "@react-router/dev/vite";
import { defineConfig } from "vite";

const usePolling = process.env.VITE_USE_POLLING === "1";
const hmrClientPort = process.env.VITE_HMR_CLIENT_PORT
  ? Number(process.env.VITE_HMR_CLIENT_PORT)
  : undefined;

export default defineConfig({
  plugins: [reactRouter()],
  resolve: {
    tsconfigPaths: true,
  },
  css: {
    preprocessorOptions: {
      scss: {
        // Bootstrap 5.3 aún usa @import y funciones globales de Sass.
        silenceDeprecations: ["import", "global-builtin", "color-functions", "if-function"],
        quietDeps: true,
      },
    },
  },
  // Pre-empaquetar en el arranque: evita que Vite re-optimice (504) en la primera visita.
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-dom/client",
      "react/jsx-runtime",
      "react/jsx-dev-runtime",
      "react-router",
      "@tanstack/react-query",
      "react-hook-form",
      "@hookform/resolvers/zod",
      "zod",
      "lucide-react",
      "react-markdown",
    ],
  },
  server: {
    host: "0.0.0.0",
    port: 8080,
    strictPort: true,
    // En Docker Desktop sobre Windows los eventos de archivo no cruzan el bind mount.
    watch: usePolling ? { usePolling: true, interval: 300 } : undefined,
    // El navegador entra por el proxy (http://localhost:8088), no por el puerto de Vite.
    hmr: hmrClientPort ? { clientPort: hmrClientPort } : undefined,
  },
});
