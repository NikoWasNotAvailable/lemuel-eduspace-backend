-- Migration: Add is_active column to classes table
-- Date: 2026-01-21
-- Description: Adds is_active boolean column to classes table with default value TRUE

-- Add is_active column to classes table
ALTER TABLE `classes` 
ADD COLUMN `is_active` BOOLEAN DEFAULT TRUE NOT NULL AFTER `region_id`;

-- Update existing classes to be active
UPDATE `classes` SET `is_active` = TRUE WHERE `is_active` IS NULL;
