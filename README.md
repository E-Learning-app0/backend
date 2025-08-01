# 🚀 Quick Setup Guide - Auth & Content Services

## Prerequisites

- Python 3.8+
- PostgreSQL database
- react (for frontend)


```sql
-- Create databases
CREATE DATABASE elearning_auth;
CREATE DATABASE elearning_content;

-- Create a user (optional)
CREATE USER elearning_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE elearning_auth TO elearning_user;
GRANT ALL PRIVILEGES ON DATABASE elearning_content TO elearning_user;
```

### 2. Auth Service Setup

```bash
cd auth-service

# Copy environment file
copy .env.example .env

# Edit .env file with your values:
# - SECRET_KEY: Generate a secure random key
# - DATABASE_URL: Your PostgreSQL connection string
# - Email settings for verification emails
# - Google OAuth client ID

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the service (Windows)
start-dev.bat

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Content Service Setup

```bash
cd content-service

# Copy environment file
copy .env.example .env

# Edit .env file with your values:
# - DATABASE_URL: Your PostgreSQL connection string
# - AUTH_SERVICE_URL: Usually http://localhost:8000

# Install dependencies
pip install -r requirements.txt

# Start the service (Windows)
start-dev.bat

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 🧪 Testing the Services

### Auth Service Endpoints:

- POST `/api/v1/register` - User registration
- POST `/api/v1/login` - User login
- GET `/api/v1/users/me` - Get current user info
- GET `/api/v1/verify-email` - Email verification

### Content Service Endpoints:

- GET `/modules` - List modules
- GET `/lessons` - List lessons
- POST `/lessons` - Create lesson (requires auth)
- GET `/quiz/debug-info` - Quiz service status

## 🔧 Environment Variables

### Auth Service (.env)

```env
SECRET_KEY=your_super_secret_jwt_key_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/elearning_auth
GOOGLE_CLIENT_ID=your_google_client_id
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_SERVER=smtp.gmail.com
FRONTEND_URL=http://localhost:5173
```

### Content Service (.env)

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/elearning_content
AUTH_SERVICE_URL=http://localhost:8000
QUIZ_MICROSERVICE_URL=http://localhost:8002/upload-quiz
```

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection**: Make sure PostgreSQL is running and credentials are correct
2. **Port Conflicts**: Auth service runs on 8000, Content service on 8080
3. **Missing Dependencies**: Run `pip install -r requirements.txt` in each service
4. **Migration Errors**: Make sure database exists before running migrations

### Health Checks:

- Auth Service: `http://localhost:8000/docs`
- Content Service: `http://localhost:8080/docs`

## 📝 Next Steps

1. Set up your frontend to connect to these services
2. Configure email settings for user verification
3. Set up Vimeo integration (optional)
4. Implement payment service integration
5. Set up production deployment with Docker
