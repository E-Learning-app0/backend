# Video Service Setup Guide

This guide explains how to set up both API.video and Vimeo for video uploads in your e-learning platform.

## 🎯 Recommended: API.video (Free & Easy)

API.video is the recommended choice because:

- ✅ **Free tier**: 10GB storage + 100GB bandwidth/month
- ✅ **No approval needed**: Start uploading immediately
- ✅ **Simple setup**: Just API key required
- ✅ **Reliable performance**: Modern video infrastructure

### API.video Setup Steps:

1. **Create Account**

   - Go to [api.video](https://api.video)
   - Sign up for free account
   - Verify your email

2. **Get API Key**

   - Login to dashboard
   - Go to API Keys section
   - Copy your API key

3. **Configure Environment**

   ```bash
   # Add to your .env file
   APIVIDEO_KEY=your_api_key_here
   ```

4. **Install Dependencies**

   ```bash
   pip install apivideo
   ```

5. **Test Setup**
   ```bash
   curl -X GET "http://localhost:8080/videos/providers/status" \
        -H "Authorization: Bearer your_jwt_token"
   ```

## 🔧 Alternative: Vimeo (Requires Approval)

Vimeo upload API requires manual approval which can take days/weeks.

### Vimeo Setup Steps:

1. **Create Vimeo Developer App**

   - Go to [developer.vimeo.com](https://developer.vimeo.com)
   - Create new app
   - Note your Client ID and Secret

2. **Request Upload Permission**

   - In your app settings, request "Upload" scope
   - Fill out the approval form explaining your use case
   - Wait for Vimeo's review (1-3 business days, can take longer)

3. **Generate Access Token**

   - Once approved, generate access token with upload scope
   - Keep this token secure

4. **Configure Environment**

   ```bash
   # Add to your .env file
   VIMEO_CLIENT_ID=your_client_id
   VIMEO_CLIENT_SECRET=your_client_secret
   VIMEO_ACCESS_TOKEN=your_access_token
   ```

5. **Install Dependencies**
   ```bash
   pip install python-vimeo
   ```

## 🚀 Using the Video Service

### API Endpoints

```bash
# Check provider status
GET /videos/providers/status

# Create video (API.video)
POST /videos/create
{
  "name": "My Lesson Video",
  "description": "Introduction to React",
  "privacy": "unlisted",
  "provider": "apivideo"
}

# Create video (Vimeo)
POST /videos/create
{
  "name": "My Lesson Video",
  "description": "Introduction to React",
  "privacy": "unlisted",
  "provider": "vimeo"
}

# Get video info
GET /videos/info/{provider}/{video_id}

# Delete video
DELETE /videos/{provider}/{video_id}

# Create lesson with video
POST /videos/lessons
{
  "moduleid": "module-uuid",
  "title": "React Basics",
  "content": "Learn React fundamentals",
  "video_url": "https://embed.api.video/vod/video_id",
  "video_id": "video_id",
  "video_provider": "apivideo"
}
```

### Frontend Integration Example

```javascript
// Check which providers are available
const checkProviders = async () => {
  const response = await fetch("/videos/providers/status");
  const status = await response.json();
  return status;
};

// Create video with preferred provider
const createVideo = async (videoData) => {
  const response = await fetch("/videos/create", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      name: videoData.title,
      description: videoData.description,
      privacy: "unlisted",
      provider: "apivideo", // or 'vimeo'
    }),
  });

  return response.json();
};

// Upload video file to the provider
const uploadVideo = async (uploadUrl, videoFile) => {
  const formData = new FormData();
  formData.append("file", videoFile);

  const response = await fetch(uploadUrl, {
    method: "POST",
    body: formData,
  });

  return response.json();
};

// Create lesson with video
const createLessonWithVideo = async (lessonData) => {
  const response = await fetch("/videos/lessons", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(lessonData),
  });

  return response.json();
};
```

## 🔄 Migration from Vimeo to API.video

If you're currently using Vimeo and want to switch:

1. **Dual Setup**: Configure both providers
2. **New Uploads**: Use API.video for new content
3. **Existing Content**: Keep Vimeo videos (they'll continue working)
4. **Gradual Migration**: Optionally migrate old videos over time

## 📊 Provider Comparison

| Feature            | API.video                     | Vimeo                        |
| ------------------ | ----------------------------- | ---------------------------- |
| Free Tier          | 10GB storage, 100GB bandwidth | Limited                      |
| Setup Time         | Instant                       | Days/weeks for approval      |
| Upload API         | Immediately available         | Requires approval            |
| Video Quality      | High                          | High                         |
| Reliability        | Good                          | Good                         |
| Cost               | Free → Paid tiers             | Free → Paid tiers            |
| **Recommendation** | ✅ **Best Choice**            | Use only if already approved |

## 🐛 Troubleshooting

### API.video Issues

- **Invalid API key**: Check your API key in dashboard
- **Quota exceeded**: Upgrade plan or wait for monthly reset
- **Upload failed**: Check file format (MP4, MOV, AVI supported)

### Vimeo Issues

- **Upload permission denied**: Your app needs upload approval from Vimeo
- **Token expired**: Generate new access token
- **Rate limiting**: Vimeo has strict rate limits

### General Issues

- **Dependencies missing**: Run `pip install -r requirements.txt`
- **Environment variables**: Check your .env file configuration
- **Network errors**: Check internet connection and API endpoints

## 🔧 Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start content service
cd content-service
uvicorn app.main:app --reload --port 8080

# Test the video service
curl -X GET "http://localhost:8080/videos/upload-guide"
```

## 📝 Notes

- The unified video service supports both providers simultaneously
- Legacy Vimeo endpoints remain available for backward compatibility
- All video metadata is stored in your database with provider information
- The `video_type` field in lessons indicates which provider was used
