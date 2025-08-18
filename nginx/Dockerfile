# NGINX Gateway for E-Learning Microservices
FROM nginx:alpine

# Install additional tools for debugging
RUN apk add --no-cache curl

# Copy custom NGINX configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/temp

# Set proper permissions
RUN chown -R nginx:nginx /var/log/nginx /var/temp

# Expose ports
EXPOSE 8000 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]
