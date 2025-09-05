# API.video Setup Guide

## 1. Get API.video Account

1. Go to [api.video](https://api.video) and create a free account
2. Navigate to your dashboard
3. Go to API Keys section
4. Copy your API Key

## 2. Configure Environment Variables

Add to your `.env` file in the content-service directory:

```bash
# API.video Configuration
APIVIDEO_KEY=your_api_video_key_here
```

## 3. Frontend Changes Applied

✅ **VimeoUploader.jsx** updated to **ApiVideoUploader**

- Removed all Vimeo references
- Updated to use API.video endpoints (`/apivideo/create-video`)
- Changed upload method to use multipart form data
- Updated video URLs to API.video format

## 4. Backend Changes Applied

✅ **content-service/app/routers/apivideo.py**

- Updated `create-video` endpoint to return `upload_token`
- Fixed parameter naming (`title` instead of `name`)

✅ **content-service/app/main.py**

- Uncommented and enabled apivideo router

## 5. API Endpoints Available

- `POST /apivideo/create-video` - Create video and get upload token
- `POST /apivideo/create-lesson` - Create lesson with API.video
- `GET /apivideo/video-info/{video_id}` - Get video details
- `DELETE /apivideo/video/{video_id}` - Delete video
- `GET /apivideo/upload-status` - Check API access

## 6. How It Works

1. **Frontend**: User selects video file in admin upload interface
2. **Backend**: Creates video record on API.video, returns video_id + upload_token
3. **Frontend**: Uploads video directly to API.video using multipart form data
4. **Backend**: Saves lesson with API.video video_id to database

## 7. Video URLs Format

Videos will have URLs like:

```
https://vod.api.video/vod/{video_id}/mp4/source.mp4
```

## 8. Benefits over Vimeo

- ✅ **Free tier available** (no cost for basic usage)
- ✅ **Better API documentation**
- ✅ **Simpler upload process** (multipart vs TUS)
- ✅ **Good video quality**
- ✅ **Fast CDN delivery**

## 9. Testing

1. Start your content service: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
2. Go to admin upload interface
3. Select a video file
4. Fill in title and course
5. Click upload - should work with API.video now!

## 10. Troubleshooting

**Error: "Missing API_VIDEO_KEY"**

- Make sure APIVIDEO_KEY is set in your .env file

**Upload fails:**

- Check your API key is valid
- Verify you haven't exceeded free tier limits
- Check network connectivity

**Video not playing:**

- API.video videos need a few minutes to process after upload
- Check the video_id is correct in your database
