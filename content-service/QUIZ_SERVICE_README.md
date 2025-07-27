# Quiz Background Service

This service automatically generates quizzes for lessons that have PDF content but no quiz_id.

## How it works

1. **Background Task**: Runs every 24 hours (configurable) to check for lessons without quiz IDs
2. **PDF Processing**: Downloads PDF content from lesson URLs
3. **Microservice Call**: Sends PDF to the quiz generation microservice at `http://localhost:8002/upload-quiz`
4. **Database Update**: Updates the lesson with the returned quiz_id

## Configuration

Environment variables (optional):

- `QUIZ_MICROSERVICE_URL` - URL of the quiz generation service (default: http://localhost:8002/upload-quiz)
- `QUIZ_GENERATION_INTERVAL_HOURS` - Hours between each run (default: 24)
- `HTTP_TIMEOUT_SECONDS` - Timeout for HTTP requests (default: 30)

## API Endpoints

### Admin Only:

- `POST /quiz/start-background-task` - Start the background task
- `POST /quiz/process-now` - Process lessons immediately
- `POST /quiz/stop-background-task` - Stop the background task

### Admin/Teacher:

- `GET /quiz/task-status` - Check background task status

## Usage

1. The background task starts automatically when the application starts
2. It will check every 24 hours for lessons with PDFs that don't have quiz_ids
3. For each such lesson, it will:
   - Download the PDF from the lesson's `pdf` field
   - Send it to your quiz microservice
   - Update the lesson with the returned quiz_id

## Manual Operation

You can manually trigger processing using:

```bash
curl -X POST "http://localhost:8000/quiz/process-now" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Or check the status:

```bash
curl -X GET "http://localhost:8000/quiz/task-status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Requirements

- Your quiz microservice must be running on `http://localhost:8002/upload-quiz`
- Lessons must have valid PDF URLs in their `pdf` field
- The quiz microservice should return `{"quizId": "some-uuid"}`
