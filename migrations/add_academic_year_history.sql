-- Migration: Add Academic Year History Tables
-- This migration adds support for tracking users' grade/class history across academic years
-- Run this on existing databases to add the new tables

-- Academic Years table - stores academic year periods
CREATE TABLE IF NOT EXISTS `academic_years` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(50) NOT NULL UNIQUE,                 -- e.g., "2024/2025"
  `start_date` DATE NOT NULL,
  `end_date` DATE NOT NULL,
  `is_current` BOOLEAN DEFAULT FALSE NOT NULL,        -- Only one should be current
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- User Academic History table - stores user's grade/class for each academic year
-- This enables viewing historical data: what class/grade a student was in during previous years
CREATE TABLE IF NOT EXISTS `user_academic_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `academic_year_id` INT NOT NULL,
  `grade` ENUM('TKA', 'TKB', 'SD1', 'SD2', 'SD3', 'SD4', 'SD5', 'SD6', 'SMP1', 'SMP2', 'SMP3') DEFAULT NULL,
  `class_id` INT DEFAULT NULL,
  `role` ENUM('admin', 'teacher', 'student') NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`academic_year_id`) REFERENCES `academic_years`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`class_id`) REFERENCES `classes`(`id`) ON DELETE SET NULL,
  UNIQUE KEY `unique_user_academic_year` (`user_id`, `academic_year_id`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- Optional: Insert the current academic year (adjust dates as needed)
-- INSERT INTO `academic_years` (`name`, `start_date`, `end_date`, `is_current`) 
-- VALUES ('2025/2026', '2025-08-01', '2026-07-31', TRUE);
