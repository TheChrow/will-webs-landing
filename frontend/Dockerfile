# Fase 0: sirve la landing estática (frontend/legacy) mientras se construye el frontend React (Fase 2).
# Imagen Nginx sin privilegios: corre como uid 101 y escucha en 8080.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY legacy/ /usr/share/nginx/html/
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
