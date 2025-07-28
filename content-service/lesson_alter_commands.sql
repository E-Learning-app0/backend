-- ALTER statements for your lesson table
-- Run these commands in your PostgreSQL database

-- Add the missing columns
ALTER TABLE public.lesson 
ADD COLUMN vimeo_id VARCHAR,
ADD COLUMN video_type VARCHAR;

-- Add indexes for better performance
CREATE INDEX idx_lesson_vimeo_id ON public.lesson(vimeo_id);
CREATE INDEX idx_lesson_video_type ON public.lesson(video_type);

-- Optional: Update existing lessons with video URLs to set video_type
UPDATE public.lesson 
SET video_type = CASE 
    WHEN video LIKE '%vimeo.com%' THEN 'vimeo'
    WHEN video LIKE '%youtube.com%' OR video LIKE '%youtu.be%' THEN 'youtube'
    WHEN video IS NOT NULL AND video != '' THEN 'external'
    ELSE NULL
END
WHERE video IS NOT NULL;

-- Optional: Extract Vimeo IDs from existing video URLs
UPDATE public.lesson 
SET vimeo_id = 
    CASE 
        WHEN video ~ 'vimeo\.com/(\d+)' THEN 
            (regexp_matches(video, 'vimeo\.com/(\d+)'))[1]
        WHEN video ~ 'player\.vimeo\.com/video/(\d+)' THEN 
            (regexp_matches(video, 'player\.vimeo\.com/video/(\d+)'))[1]
        ELSE NULL
    END
WHERE video_type = 'vimeo';

-- Verify the changes
SELECT id, moduleid, title, content, video, orderindex, createdat, title_fr, completed, pdf, quiz_id, vimeo_id, video_type
FROM public.lesson
LIMIT 5;
