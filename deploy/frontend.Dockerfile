FROM node:22-bookworm-slim AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.12.1 --activate
COPY my-nuxt-app/package.json my-nuxt-app/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY my-nuxt-app/nuxt.config.ts my-nuxt-app/tsconfig.json ./
COPY my-nuxt-app/app ./app
COPY my-nuxt-app/public ./public
# Empty means same-origin /api. Never embed an API/model secret in the public bundle.
ENV NUXT_PUBLIC_API_BASE=""
RUN pnpm generate

FROM nginx:1.28-alpine
RUN apk add --no-cache ca-certificates
COPY --from=build /app/.output/public /usr/share/nginx/html
COPY deploy/nginx/default.conf.template /etc/nginx/templates/default.conf.template
ENV NGINX_ENVSUBST_FILTER="^(RAG_API_KEY|RAG_PUBLIC_ORIGIN|RAG_API_ORIGIN|RAG_API_HOST)$"
EXPOSE 8080
