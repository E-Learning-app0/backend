# Vimeo Integration Setup Guide

## 🎯 Overview

This setup adds Vimeo video management capabilities to your e-learning platform.

## 📋 Prerequisites

1. Vimeo Developer Account
2. PostgreSQL Database
3. Python environment with pip

## 🚀 Installation Steps

### 1. Install Required Package

```bash
cd content-service
pip install python-vimeo
```

### 2. Get Vimeo API Credentials

1. Go to https://developer.vimeo.com/
2. Create a new app
3. Generate access token with scopes:
   - `public`
   - `private`
   - `upload`
   - `edit`
   - `video_files`

### 3. Configure Environment Variables

Add to your `.env` file:

```env
VIMEO_CLIENT_ID=your_vimeo_client_id
VIMEO_CLIENT_SECRET=your_vimeo_client_secret
VIMEO_ACCESS_TOKEN=your_vimeo_access_token
```

### 4. Database Migration

Run the SQL commands in `migration_vimeo.sql`:

```bash
psql -d your_database -f migration_vimeo.sql
```

### 5. Start the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 🔗 Available Endpoints

### Vimeo Management (`/vimeo/`)

- `POST /vimeo/create-upload` - Create upload ticket
- `PATCH /vimeo/update-metadata/{video_id}` - Update video metadata
- `POST /vimeo/create-lesson` - Create lesson with Vimeo video
- `GET /vimeo/video-info/{video_id}` - Get video information
- `DELETE /vimeo/video/{video_id}` - Delete video

### Admin Statistics (`/admin/`)

- `GET /admin/stats/modules` - Total modules count
- `GET /admin/stats/lessons` - Total lessons count
- `GET /admin/stats/videos` - Total videos count
- `GET /admin/stats/quizzes` - Total quizzes count
- `GET /admin/stats/summary` - Complete overview
- `GET /admin/lessons/without-videos` - Lessons needing videos
- `GET /admin/lessons/without-quizzes` - Lessons needing quizzes

## 📊 Usage Examples

### Upload Video to Vimeo

```python
# Frontend uploads file directly to Vimeo using the upload_url
# Then calls your API to create the lesson

POST /vimeo/create-lesson
{
  "moduleid": "module-uuid",
  "title": "Lesson 1: Introduction",
  "video_url": "https://player.vimeo.com/video/123456789",
  "vimeo_id": "123456789",
  "video_type": "vimeo",
  "orderindex": 1
}
```

### Get Admin Statistics

```python
GET /admin/stats/summary
# Returns:
{
  "modules": 5,
  "lessons": 25,
  "videos": 20,
  "quizzes": 15,
  "pdfs": 22
}
```

## 🔧 Configuration

### Vimeo Privacy Settings

Videos are uploaded as "unlisted" by default. Options:

- `private` - Only you can view
- `unlisted` - Anyone with link can view
- `public` - Publicly searchable

### Video URL Formats Supported

- `https://vimeo.com/123456789`
- `https://player.vimeo.com/video/123456789`
- `https://vimeo.com/channels/name/123456789`

## 🚨 Security Notes

1. Keep Vimeo credentials secure
2. Use HTTPS in production
3. Implement proper JWT authentication
4. Validate user roles for admin endpoints

## 🔍 Troubleshooting

### Common Issues

1. **"Vimeo integration not configured"**

   - Check environment variables
   - Verify credentials are valid

2. **Upload fails**

   - Check file size limits
   - Verify internet connection
   - Check Vimeo account quota

3. **Video not found**
   - Ensure video ID is correct
   - Check video privacy settings

### Logs Location

- Application logs: Console output
- Error details: FastAPI exception responses

## 📈 Monitoring

- Check `/admin/stats/summary` for platform overview
- Monitor video upload success rates
- Track lessons without videos/quizzes

## 🎨 Frontend Integration

Your frontend can now:

1. Upload videos directly to Vimeo
2. Create lessons with video URLs
3. Display admin statistics
4. Manage content through API endpoints

## 🔄 Next Steps

1. Add video transcoding webhooks
2. Implement video analytics
3. Add bulk upload capabilities
4. Create video playlist management
