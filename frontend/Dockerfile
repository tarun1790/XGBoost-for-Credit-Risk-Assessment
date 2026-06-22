# Stage 1: Build React Application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install node dependencies
RUN npm ci

# Copy frontend source files
COPY . .

# Compile production bundle
RUN npm run build

# Stage 2: Serve Bundle via Nginx
FROM nginx:stable-alpine

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
