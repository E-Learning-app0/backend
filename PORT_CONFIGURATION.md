# E-Learning App Port Configuration

## 🎯 Production Port Layout

```
🌐 NGINX Gateway:     8000  ← Main entry point (Frontend connects here)
🔐 Auth Service:      8001  ← Authentication & JWT tokens
📚 Content Service:   8002  ← Lessons, modules, quiz, vimeo
🤖 Agent Service:     8004  ← AI/Agent functionality
💳 Payment Service:   8005  ← Payment processing & subscriptions
```

## 🔄 Request Flow

```
Frontend → NGINX:8000 → Routes to:
                    ├── /api/v1/refresh       → Auth:8001
                    ├── /api/v1/login         → Auth:8001
                    ├── /api/v1/register      → Auth:8001
                    ├── /api/v1/users/        → Auth:8001
                    ├── /api/v1/content/      → Content:8002
                    ├── /api/v1/agent/        → Agent:8004
                    └── /api/v1/payment/      → Payment:8005
```

## 🚀 Quick Start Commands

### Start All Services:

```bash
# Linux/Mac
chmod +x start-all-services.sh
./start-all-services.sh

# Windows
start-all-services.bat
```

### Stop All Services:

```bash
# Linux/Mac
./stop-all-services.sh

# Windows
stop-all-services.bat
```

### Start Individual Services:

```bash
# Auth Service
cd auth-service && python -m uvicorn app.main:app --port 8001

# Content Service
cd content-service && python -m uvicorn app.main:app --port 8002

# Payment Service
cd payment-service && python -m uvicorn app.main:app --port 8005

# NGINX Gateway
nginx -c $(pwd)/nginx.conf
```

## 🔑 Frontend Configuration

```javascript
// ✅ Single API base URL for all requests
const API_BASE = "http://localhost:8000/api/v1";

// Critical endpoints
const AUTH_ENDPOINTS = {
  refresh: `${API_BASE}/refresh`, // Token refresh (prevents logout)
  login: `${API_BASE}/login`,
  register: `${API_BASE}/register`,
  me: `${API_BASE}/users/me`,
};

const CONTENT_ENDPOINTS = {
  lessons: `${API_BASE}/content/lessons`,
  modules: `${API_BASE}/content/modules`,
  quiz: `${API_BASE}/content/quiz`,
  vimeo: `${API_BASE}/content/vimeo`,
};

const PAYMENT_ENDPOINTS = {
  subscribe: `${API_BASE}/payment/subscribe`,
  billing: `${API_BASE}/payment/billing`,
};
```

## 🎯 Health Checks

```bash
# Gateway health
curl http://localhost:8000/health

# Service health
curl http://localhost:8001/health  # Auth
curl http://localhost:8002/health  # Content
curl http://localhost:8003/health  # Payment
```

## 🔒 Security Notes

- All services only accept connections from localhost (127.0.0.1)
- NGINX handles CORS and security headers
- Rate limiting configured in NGINX
- Services don't need individual CORS setup

## 📊 Port Monitoring

```bash
# Check what's running on our ports
netstat -tulpn | grep -E ':(8000|8001|8002|8005)'

# Or on Windows
netstat -an | findstr ":8000 :8001 :8002 :8005"
```
