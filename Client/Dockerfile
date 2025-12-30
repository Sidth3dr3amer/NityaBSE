# Multi-stage build for Client Frontend
FROM node:18-alpine AS base

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (if any build step needed)
RUN npm install

# Copy all frontend files
COPY . .

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static files from base stage
COPY --from=base /app/*.html /usr/share/nginx/html/
COPY --from=base /app/*.css /usr/share/nginx/html/
COPY --from=base /app/*.js /usr/share/nginx/html/

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh


# Use custom start script
CMD ["/start.sh"]
