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
RUN npm run build


# ----------------------------------------------------------------- production
FROM nginx:1.27-alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
