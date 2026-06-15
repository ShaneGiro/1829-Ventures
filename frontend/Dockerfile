# Production build: compile the SPA, serve it with nginx (proxies /api to FastAPI).
# v1 dev uses the Vite dev server; this image is for the prod compose stack.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# The prod compose mounts ../nginx/nginx.conf to /etc/nginx/conf.d/default.conf
# (same pattern the repo uses for postgres/minio config), so it is not baked in.
EXPOSE 80
