-- Migration script to add new fields to cameras table and create allowed_persons table
-- Run this script in your PostgreSQL database

-- Add is_restricted_zone column to cameras table (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cameras' AND column_name = 'is_restricted_zone'
    ) THEN
        ALTER TABLE cameras ADD COLUMN is_restricted_zone BOOLEAN NOT NULL DEFAULT FALSE;
        RAISE NOTICE 'Added is_restricted_zone column to cameras table';
    ELSE
        RAISE NOTICE 'is_restricted_zone column already exists';
    END IF;
END $$;

-- Create allowed_persons table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS allowed_persons (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on camera_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_allowed_persons_camera_id ON allowed_persons(camera_id);

-- Add comment
COMMENT ON TABLE allowed_persons IS 'Stores images of allowed persons for cameras';

