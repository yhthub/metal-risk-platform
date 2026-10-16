# Run Nuxt generation on the development/build machine BEFORE packaging this image.
# The small ECS never installs Node packages or runs a frontend production build.
FROM nginx:1.28-alpine
RUN apk add --no-cache ca-certificates
COPY my-nuxt-app/.output/public /usr/share/nginx/html
COPY deploy/nginx/default.conf.template /etc/nginx/templates/default.conf.template
ENV NGINX_ENVSUBST_FILTER="^(RAG_API_KEY|RAG_PUBLIC_ORIGIN|RAG_API_ORIGIN|RAG_API_HOST)$"
EXPOSE 8080
