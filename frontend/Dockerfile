# Frontend Dockerfile for Stock Backtest System
# Multi-stage build for optimized production image

# Stage 1: Build the React application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for build)
# Use npm install instead of npm ci since package-lock.json might not exist
RUN npm install && npm cache clean --force

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create a script to replace environment variables at runtime
RUN echo '#!/bin/sh' > /docker-entrypoint.d/40-envsubst-on-templates.sh && \
    echo 'set -e' >> /docker-entrypoint.d/40-envsubst-on-templates.sh && \
    echo 'echo "Replacing environment variables..."' >> /docker-entrypoint.d/40-envsubst-on-templates.sh && \
    echo 'find /usr/share/nginx/html -type f -name "*.js" -exec sed -i "s|VITE_API_BASE_URL_PLACEHOLDER|${API_BASE_URL:-http://localhost:5000}|g" {} +' >> /docker-entrypoint.d/40-envsubst-on-templates.sh && \
    chmod +x /docker-entrypoint.d/40-envsubst-on-templates.sh

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Nginx will be started by the base image's entrypoint
