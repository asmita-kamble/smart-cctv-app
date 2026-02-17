-- Migration script to add RTSP configuration fields to cameras table
-- Run this SQL script directly on your PostgreSQL database

-- Add RTSP username column (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cameras' AND column_name = 'rtsp_username'
    ) THEN
        ALTER TABLE cameras ADD COLUMN rtsp_username VARCHAR(100);
        RAISE NOTICE 'Added rtsp_username column';
    ELSE
        RAISE NOTICE 'rtsp_username column already exists';
    END IF;
END $$;

-- Add RTSP password column (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cameras' AND column_name = 'rtsp_password'
    ) THEN
        ALTER TABLE cameras ADD COLUMN rtsp_password VARCHAR(255);
        RAISE NOTICE 'Added rtsp_password column';
    ELSE
        RAISE NOTICE 'rtsp_password column already exists';
    END IF;
END $$;

-- Add RTSP path column (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cameras' AND column_name = 'rtsp_path'
    ) THEN
        ALTER TABLE cameras ADD COLUMN rtsp_path VARCHAR(255);
        RAISE NOTICE 'Added rtsp_path column';
    ELSE
        RAISE NOTICE 'rtsp_path column already exists';
    END IF;
END $$;

-- Verify the migration
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'cameras'
AND column_name IN ('rtsp_username', 'rtsp_password', 'rtsp_path')
ORDER BY column_name;

