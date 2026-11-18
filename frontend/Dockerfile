# syntax=docker/dockerfile:1
FROM node:22-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./


# ---------------------------------------------------------------- development
FROM base AS development
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]


# ---------------------------------------------------------------------- build
FROM base AS build
RUN npm ci
COPY . .
RUN VITE_API_URL=/api/v1 npm run build


# ----------------------------------------------------------------- production
FROM nginx:1.30.6-alpine3.24 AS production
COPY nginx-main.conf /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER nginx
EXPOSE 8080
