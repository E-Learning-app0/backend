# Frontend API Configuration Guide

## 🎯 Single Gateway URL

Your frontend should **ONLY** communicate with:

```javascript
const API_BASE = "http://localhost:8000/api/v1";
```

## 📋 Complete Frontend API Endpoints

### 🔐 Authentication Endpoints (Direct to Auth Service)

```javascript
const AUTH_API = {
  BASE: `${API_BASE}`,

  // Authentication
  LOGIN: `${API_BASE}/login`,
  REGISTER: `${API_BASE}/register`,
  REFRESH: `${API_BASE}/refresh`, // 🔑 Critical for preventing logout

  // User info
  USER_INFO: `${API_BASE}/users/me`,
  TOKEN_INFO: `${API_BASE}/token/info`,
};
```

### 📚 Content Endpoints (Routed to Content Service)

```javascript
const CONTENT_API = {
  BASE: `${API_BASE}/content`,

  // Lessons
  LESSONS: `${API_BASE}/content/lessons`,
  LESSON_BY_ID: (id) => `${API_BASE}/content/lessons/${id}`,

  // Modules
  MODULES: `${API_BASE}/content/modules`,
  MODULE_BY_ID: (id) => `${API_BASE}/content/modules/${id}`,

  // Quiz
  QUIZ: `${API_BASE}/content/quiz`,
  QUIZ_BY_LESSON: (lessonId) => `${API_BASE}/content/quiz/lesson/${lessonId}`,

  // User Progress
  USER_PROGRESS: `${API_BASE}/content/user-lesson-progress`,
  ALL_PROGRESS: `${API_BASE}/content/user-lesson-progress/all`,
  USER_PROGRESS_BY_ID: (userId) =>
    `${API_BASE}/content/user-lesson-progress/user/${userId}`,

  // Module Progress
  MODULE_PROGRESS: `${API_BASE}/content/users-progress`,
  MODULE_PROGRESS_BY_USER: (userId) =>
    `${API_BASE}/content/users-progress/user/${userId}`,

  // Vimeo
  VIMEO: `${API_BASE}/content/vimeo`,
  VIMEO_UPLOAD: `${API_BASE}/content/vimeo/upload`,
};
```

### 🤖 Agent Endpoints (Routed to Agent Service)

```javascript
const AGENT_API = {
  BASE: `${API_BASE}/agent`,

  // AI Chat
  CHAT: `${API_BASE}/agent/chat`,
  CHAT_HISTORY: `${API_BASE}/agent/chat/history`,

  // Content Generation
  GENERATE_QUIZ: `${API_BASE}/agent/generate/quiz`,
  GENERATE_LESSON: `${API_BASE}/agent/generate/lesson`,

  // Analysis
  ANALYZE_PROGRESS: `${API_BASE}/agent/analyze/progress`,
  ANALYZE_CONTENT: `${API_BASE}/agent/analyze/content`,

  // Recommendations
  RECOMMEND_LESSONS: `${API_BASE}/agent/recommend/lessons`,
  RECOMMEND_STUDY_PATH: `${API_BASE}/agent/recommend/study-path`,
};
```

### 💳 Payment Endpoints (Routed to Payment Service)

```javascript
const PAYMENT_API = {
  BASE: `${API_BASE}/payment`,

  // Subscriptions
  SUBSCRIBE: `${API_BASE}/payment/subscribe`,
  SUBSCRIPTIONS: `${API_BASE}/payment/subscriptions`,

  // Billing
  BILLING: `${API_BASE}/payment/billing`,
  BILLING_HISTORY: `${API_BASE}/payment/billing/history`,

  // Payments
  PROCESS_PAYMENT: `${API_BASE}/payment/process`,
  PAYMENT_STATUS: (paymentId) => `${API_BASE}/payment/status/${paymentId}`,
};
```

## 🔧 Usage Examples

### Authentication with Token Refresh

```javascript
class AuthService {
  static async login(email, password) {
    const response = await fetch(AUTH_API.LOGIN, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return response.json();
  }

  static async refreshToken() {
    const currentToken = localStorage.getItem("token");
    const response = await fetch(AUTH_API.REFRESH, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${currentToken}`,
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      return data.access_token;
    }
    throw new Error("Token refresh failed");
  }
}
```

### Content Service Calls

```javascript
class ContentService {
  static async getAllUserProgress() {
    const token = localStorage.getItem("token");
    const response = await fetch(CONTENT_API.ALL_PROGRESS, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.json();
  }

  static async getUserProgress(userId) {
    const token = localStorage.getItem("token");
    const response = await fetch(CONTENT_API.USER_PROGRESS_BY_ID(userId), {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.json();
  }
}
```

### Agent Service Calls

```javascript
class AgentService {
  static async chatWithAI(message) {
    const token = localStorage.getItem("token");
    const response = await fetch(AGENT_API.CHAT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });
    return response.json();
  }

  static async generateQuiz(lessonId) {
    const token = localStorage.getItem("token");
    const response = await fetch(AGENT_API.GENERATE_QUIZ, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ lessonId }),
    });
    return response.json();
  }
}
```

## 🔄 Request Flow

```
Frontend Request → NGINX:8000 → Routes to appropriate service:

http://localhost:8000/api/v1/refresh              → Auth:8001
http://localhost:8000/api/v1/content/lessons      → Content:8002
http://localhost:8000/api/v1/agent/chat          → Agent:8004
http://localhost:8000/api/v1/payment/subscribe   → Payment:8005
```

## ⚠️ Important Notes

1. **Never access services directly** - Always go through the gateway
2. **All requests** must include proper Authorization headers
3. **Token refresh** is critical to prevent user logout
4. **CORS is handled** by NGINX gateway only
5. **Rate limiting** is applied at the gateway level

## 🎯 Migration Checklist

- [ ] Replace all `localhost:8080` with `localhost:8000/api/v1/content`
- [ ] Replace all `localhost:8002` with `localhost:8000/api/v1/content`
- [ ] Replace all `localhost:8001` with `localhost:8000/api/v1`
- [ ] Add `/content/` prefix for content service endpoints
- [ ] Add `/agent/` prefix for agent service endpoints
- [ ] Add `/payment/` prefix for payment service endpoints
- [ ] Test token refresh functionality
- [ ] Verify all API calls work through gateway
