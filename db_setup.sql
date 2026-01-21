CREATE TABLE `regions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL UNIQUE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `classes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `region_id` INT DEFAULT NULL,
  `is_active` BOOLEAN DEFAULT TRUE NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`region_id`) REFERENCES `regions`(`id`) ON DELETE SET NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nis` VARCHAR(50) UNIQUE,                                -- Nomor Induk Siswa (jika siswa)
  `password` VARCHAR(255) NOT NULL,                        -- Simpan hash, bukan plaintext
  `parent_password` VARCHAR(255) DEFAULT NULL,             -- Parent password for student accounts
  `name` VARCHAR(100) NOT NULL,
  `role` ENUM('admin', 'teacher', 'student') DEFAULT 'student',
  `grade` ENUM('TKA', 'TKB', 'SD1', 'SD2', 'SD3', 'SD4', 'SD5', 'SD6', 'SMP1', 'SMP2', 'SMP3') DEFAULT NULL,
  `gender` ENUM('male', 'female') DEFAULT NULL,
  `email` VARCHAR(100) UNIQUE,
  `region_id` INT DEFAULT NULL,
  `class_id` INT DEFAULT NULL,
  `dob` DATE DEFAULT NULL,
  `birth_place` VARCHAR(100) DEFAULT NULL,                 -- Tempat lahir
  `address` TEXT DEFAULT NULL,                             -- Alamat lengkap
  `religion` ENUM('islam', 'christian', 'catholic', 'hindu', 'buddhism', 'confucianism', 'other') DEFAULT NULL,  -- Agama
  `status` ENUM('active', 'inactive', 'suspended', 'graduated') DEFAULT 'active',  -- Status pengguna
  `profile_picture` VARCHAR(500) DEFAULT NULL,             -- Path to profile picture file
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`region_id`) REFERENCES `regions`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`class_id`) REFERENCES `classes`(`id`) ON DELETE SET NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `subjects` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `class_id` INT NOT NULL,
  FOREIGN KEY (`class_id`) REFERENCES `classes`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_class_subject` (`class_id`, `name`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `teacher_subjects` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `teacher_id` INT NOT NULL,
  `subject_id` INT NOT NULL,
  FOREIGN KEY (`teacher_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_teacher_subject` (`teacher_id`, `subject_id`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `type` ENUM('general', 'announcement', 'assignment', 'event', 'payment') DEFAULT 'general',
  `nominal` DECIMAL(10, 2) DEFAULT NULL,               -- Optional, for payment notifications
  `date` DATETIME DEFAULT NULL,                        -- Optional, for events and assignments
  `is_scheduled` TINYINT(1) DEFAULT 0 NOT NULL,        -- Boolean: 0 = False, 1 = True
  `image` VARCHAR(500) DEFAULT NULL,                   -- Path to notification image
  `link` VARCHAR(500) DEFAULT NULL,                    -- Optional URL link for notification redirect
  `created_by` INT DEFAULT NULL,                       -- Who created this notification
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `user_notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `notification_id` INT NOT NULL,
  `is_read` BOOLEAN DEFAULT FALSE,
  `read_at` TIMESTAMP NULL DEFAULT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`notification_id`) REFERENCES `notifications`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_user_notification` (`user_id`, `notification_id`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `sessions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `subject_id` INT NOT NULL,
  `session_no` INT NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `date` DATE NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`subject_id`) REFERENCES `subjects`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `unique_subject_session_no` (`subject_id`, `session_no`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `session_attachments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` INT NOT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `type` ENUM('material', 'assignment', 'other') DEFAULT 'material',
  `filename` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `file_size` BIGINT NOT NULL,
  `content_type` VARCHAR(100) NOT NULL,
  `uploaded_by` INT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`uploaded_by`) REFERENCES `users`(`id`) ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `assignment_submissions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` INT NOT NULL,
  `student_id` INT NOT NULL,
  `filename` VARCHAR(255) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `grade` DECIMAL(5, 2) DEFAULT NULL,
  `feedback` TEXT DEFAULT NULL,
  `submitted_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`student_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `admin_login_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_user_id` INT NOT NULL,                        -- FK ke tabel users
  `admin_name` VARCHAR(100) NOT NULL,                 -- Nama admin yang login
  `admin_email` VARCHAR(100) NOT NULL,                -- Email admin yang login
  `login_time` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,  -- Waktu login
  `logout_time` DATETIME DEFAULT NULL,                -- Waktu logout
  `session_token` VARCHAR(255) NOT NULL,              -- Token sesi (misalnya JWT)
  `ip_address` VARCHAR(45) DEFAULT NULL,              -- IP address (support IPv6)
  `user_agent` VARCHAR(500) DEFAULT NULL,             -- Browser/device info
  FOREIGN KEY (`admin_user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- Admin Activity Logs table - stores admin CRUD operations for audit trail
CREATE TABLE `admin_activity_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `admin_id` INT NOT NULL,
  `admin_name` VARCHAR(100) NOT NULL,
  `action` ENUM('create', 'read', 'update', 'delete') NOT NULL,
  `entity_type` ENUM('user', 'class', 'subject', 'session', 'notification', 'promotion', 'teacher_subject', 'region', 'banner', 'assignment', 'academic_year') NOT NULL,
  `entity_id` INT DEFAULT NULL,
  `entity_name` VARCHAR(255) DEFAULT NULL,
  `details` TEXT DEFAULT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(500) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`admin_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- Banners table - stores promotional banners per region
CREATE TABLE `banners` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `image_url` VARCHAR(255) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `region_id` INT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`region_id`) REFERENCES `regions`(`id`) ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- Promotion History table - stores mass promotion records for undo capability
CREATE TABLE `promotion_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `promotion_date` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  `details` JSON NOT NULL,                             -- Stores list of {student_id, old_grade, old_class_id, new_grade, new_class_id, status}
  `class_mapping` JSON DEFAULT NULL,                   -- Stores {old_class_id: new_class_id} for all duplicated classes
  `status` ENUM('applied', 'reverted') DEFAULT 'applied' NOT NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- Academic Years table - stores academic year periods
CREATE TABLE `academic_years` (
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
CREATE TABLE `user_academic_history` (
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
