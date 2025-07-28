-- Add Vimeo-specific columns to the lesson table
ALTER TABLE lesson 
ADD COLUMN IF NOT EXISTS vimeo_id VARCHAR,
ADD COLUMN IF NOT EXISTS video_type VARCHAR;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_lesson_vimeo_id ON lesson(vimeo_id);
CREATE INDEX IF NOT EXISTS idx_lesson_video_type ON lesson(video_type);

-- Update existing lessons with video URLs to set video_type
UPDATE lesson 
SET video_type = CASE 
    WHEN video LIKE '%vimeo.com%' THEN 'vimeo'
    WHEN video LIKE '%youtube.com%' OR video LIKE '%youtu.be%' THEN 'youtube'
    WHEN video IS NOT NULL AND video != '' THEN 'external'
    ELSE NULL
END
WHERE video IS NOT NULL;

-- Extract Vimeo IDs from existing video URLs
UPDATE lesson 
SET vimeo_id = 
    CASE 
        WHEN video ~ 'vimeo\.com/(\d+)' THEN 
            (regexp_matches(video, 'vimeo\.com/(\d+)'))[1]
        WHEN video ~ 'player\.vimeo\.com/video/(\d+)' THEN 
            (regexp_matches(video, 'player\.vimeo\.com/video/(\d+)'))[1]
        ELSE NULL
    END
WHERE video_type = 'vimeo';
