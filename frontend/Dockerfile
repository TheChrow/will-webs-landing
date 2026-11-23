# syntax=docker/dockerfile:1.7
# ---------- deps ----------
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

# ---------- dev (Vite con HMR) ----------
FROM deps AS dev
COPY . .
# Vite escribe su caché en node_modules/.vite: el usuario node debe poder escribir.
RUN chown -R node:node /app
USER node
EXPOSE 8080
CMD ["npm", "run", "dev"]

# ---------- build (pre-render + CSP) ----------
FROM deps AS build
# Públicas (se incrustan en el JS): clave de sitio Turnstile y URL canónica.
ARG VITE_TURNSTILE_SITE_KEY=""
ARG VITE_SITE_URL=""
ENV VITE_TURNSTILE_SITE_KEY=$VITE_TURNSTILE_SITE_KEY VITE_SITE_URL=$VITE_SITE_URL
COPY . .
RUN npm run typecheck && npm test && npm run build \
 && node scripts/csp.mjs build/client build/csp.conf

# ---------- prod (Nginx sin privilegios, solo estáticos) ----------
FROM nginxinc/nginx-unprivileged:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build/csp.conf /etc/nginx/csp.conf
COPY --from=build /app/build/client/ /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
