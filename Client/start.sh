#!/bin/sh
# Generate config.js with environment variable at runtime
cat > /usr/share/nginx/html/config.js << EOF
window.ENV = {
    VITE_API_URL: '${VITE_API_URL:-http://localhost:5000/api}'
};
EOF

# Start nginx
nginx -g "daemon off;"
