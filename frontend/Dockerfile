# ==============================================================================
# Aegis AI Fraud Ops - Frontend Dashboard Dockerfile
# Multi-stage lean build with Node.js & unprivileged Nginx
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build production static bundle
# ------------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Serve with lightweight Nginx
# ------------------------------------------------------------------------------
FROM nginx:alpine-slim AS runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
