-- =====================================================================
-- Kannada for Everyone: MySQL Database Schema
-- Character Set: utf8mb4, Collation: utf8mb4_unicode_ci
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `kannada_everyone`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `kannada_everyone`;

-- 1. Users table
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `mother_tongue` ENUM('mr', 'hi', 'en') NOT NULL DEFAULT 'en',
  `level` INT NOT NULL DEFAULT 1,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_login_at` TIMESTAMP NULL,
  INDEX `idx_users_email` (`email`),
  INDEX `idx_users_level` (`level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. User Settings table (1:1 with users)
CREATE TABLE IF NOT EXISTS `user_settings` (
  `user_id` INT PRIMARY KEY,
  `daily_goal_minutes` INT NOT NULL DEFAULT 15,
  `preferred_city` VARCHAR(100) DEFAULT 'Bengaluru',
  `voice_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
  `interests_json` JSON NULL,
  `timezone` VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_user_settings_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Situations table (reusable role-play scenarios)
CREATE TABLE IF NOT EXISTS `situations` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `slug` VARCHAR(100) NOT NULL UNIQUE,
  `title` VARCHAR(200) NOT NULL,
  `description` TEXT NOT NULL,
  `category` VARCHAR(100) NOT NULL,
  `difficulty_level` INT NOT NULL DEFAULT 1,
  `ai_role` VARCHAR(150) NOT NULL,
  `system_hint` TEXT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_situations_slug` (`slug`),
  INDEX `idx_situations_category` (`category`),
  INDEX `idx_situations_level` (`difficulty_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Lessons table
CREATE TABLE IF NOT EXISTS `lessons` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `slug` VARCHAR(100) NOT NULL UNIQUE,
  `title` VARCHAR(200) NOT NULL,
  `description` TEXT NOT NULL,
  `level` INT NOT NULL DEFAULT 1,
  `lesson_order` INT NOT NULL DEFAULT 1,
  `estimated_minutes` INT NOT NULL DEFAULT 10,
  `content_json` JSON NOT NULL,
  `pass_score` INT NOT NULL DEFAULT 70,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_lessons_level_order` (`level`, `lesson_order`),
  INDEX `idx_lessons_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Conversation Sessions table
CREATE TABLE IF NOT EXISTS `conversation_sessions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `situation_id` INT NULL,
  `mode` ENUM('text', 'voice') NOT NULL DEFAULT 'text',
  `started_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `ended_at` TIMESTAMP NULL,
  `status` ENUM('active', 'completed', 'abandoned') NOT NULL DEFAULT 'active',
  `summary` TEXT NULL,
  `assessment_json` JSON NULL,
  CONSTRAINT `fk_conv_sess_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conv_sess_sit` FOREIGN KEY (`situation_id`) REFERENCES `situations` (`id`) ON DELETE SET NULL,
  INDEX `idx_conv_sess_user` (`user_id`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Conversation Messages table
CREATE TABLE IF NOT EXISTS `conversation_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` INT NOT NULL,
  `speaker` ENUM('user', 'assistant') NOT NULL,
  `message_text` TEXT NOT NULL,
  `transliteration` TEXT NULL,
  `translation` TEXT NULL,
  `feedback_json` JSON NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_conv_msg_sess` FOREIGN KEY (`session_id`) REFERENCES `conversation_sessions` (`id`) ON DELETE CASCADE,
  INDEX `idx_conv_msg_session_time` (`session_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Vocabulary Library table
CREATE TABLE IF NOT EXISTS `vocabulary` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `kannada_text` VARCHAR(200) NOT NULL,
  `transliteration` VARCHAR(200) NOT NULL,
  `english_meaning` VARCHAR(255) NOT NULL,
  `hindi_meaning` VARCHAR(255) NOT NULL,
  `marathi_meaning` VARCHAR(255) NOT NULL,
  `example_kannada` TEXT NULL,
  `example_transliteration` TEXT NULL,
  `example_translation_json` JSON NULL,
  `category` VARCHAR(100) NOT NULL,
  `level` INT NOT NULL DEFAULT 1,
  `audio_reference` VARCHAR(255) NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_kannada_cat` (`kannada_text`, `category`),
  INDEX `idx_vocab_cat_level` (`category`, `level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. User Vocabulary table (personal saved words and spaced repetition state)
CREATE TABLE IF NOT EXISTS `user_vocabulary` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `vocabulary_id` INT NOT NULL,
  `ease_factor` FLOAT NOT NULL DEFAULT 2.5,
  `interval_days` INT NOT NULL DEFAULT 0,
  `repetitions` INT NOT NULL DEFAULT 0,
  `last_rating` ENUM('Again', 'Hard', 'Good', 'Easy') NULL,
  `last_reviewed_at` TIMESTAMP NULL,
  `next_review_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `mastery_status` ENUM('learning', 'reviewing', 'mastered') NOT NULL DEFAULT 'learning',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_user_vocab` (`user_id`, `vocabulary_id`),
  CONSTRAINT `fk_user_vocab_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_vocab_vocab` FOREIGN KEY (`vocabulary_id`) REFERENCES `vocabulary` (`id`) ON DELETE CASCADE,
  INDEX `idx_user_vocab_next_rev` (`user_id`, `next_review_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Vocabulary Review History table
CREATE TABLE IF NOT EXISTS `vocabulary_review_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_vocabulary_id` INT NOT NULL,
  `rating` ENUM('Again', 'Hard', 'Good', 'Easy') NOT NULL,
  `previous_interval_days` INT NOT NULL,
  `new_interval_days` INT NOT NULL,
  `reviewed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_vocab_rev_user_vocab` FOREIGN KEY (`user_vocabulary_id`) REFERENCES `user_vocabulary` (`id`) ON DELETE CASCADE,
  INDEX `idx_vocab_rev_hist_time` (`user_vocabulary_id`, `reviewed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. User Mistakes table
CREATE TABLE IF NOT EXISTS `user_mistakes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `mistake_type` ENUM('grammar', 'vocabulary', 'word_order', 'sentence_construction', 'pronunciation', 'other') NOT NULL DEFAULT 'other',
  `original_text` TEXT NOT NULL,
  `suggested_text` TEXT NOT NULL,
  `explanation` TEXT NULL,
  `normalized_key` VARCHAR(255) NOT NULL,
  `occurrence_count` INT NOT NULL DEFAULT 1,
  `first_seen_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `last_seen_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `is_resolved` BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE KEY `uq_user_mistake_key` (`user_id`, `normalized_key`),
  CONSTRAINT `fk_user_mistakes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  INDEX `idx_user_mistakes_type` (`user_id`, `mistake_type`, `is_resolved`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Assessments table (quizzes, conversation assessments, speaking feedback)
CREATE TABLE IF NOT EXISTS `assessments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `lesson_id` INT NULL,
  `session_id` INT NULL,
  `assessment_type` ENUM('lesson_quiz', 'vocab_recall', 'conversation', 'speaking', 'pronunciation') NOT NULL,
  `score` FLOAT NOT NULL DEFAULT 0.0,
  `max_score` FLOAT NOT NULL DEFAULT 100.0,
  `feedback_json` JSON NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_assessments_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_assessments_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_assessments_session` FOREIGN KEY (`session_id`) REFERENCES `conversation_sessions` (`id`) ON DELETE SET NULL,
  INDEX `idx_assessments_user_time` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. User Lesson Progress table
CREATE TABLE IF NOT EXISTS `user_lesson_progress` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `lesson_id` INT NOT NULL,
  `status` ENUM('not_started', 'in_progress', 'completed') NOT NULL DEFAULT 'not_started',
  `attempt_count` INT NOT NULL DEFAULT 0,
  `best_score` FLOAT NOT NULL DEFAULT 0.0,
  `last_score` FLOAT NOT NULL DEFAULT 0.0,
  `started_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `completed_at` TIMESTAMP NULL,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_user_lesson` (`user_id`, `lesson_id`),
  CONSTRAINT `fk_ulp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ulp_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`id`) ON DELETE CASCADE,
  INDEX `idx_ulp_user_status` (`user_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Daily Activity table (qualifying learning activity and streaks)
CREATE TABLE IF NOT EXISTS `daily_activity` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `activity_date` DATE NOT NULL,
  `minutes_spent` INT NOT NULL DEFAULT 0,
  `lessons_completed` INT NOT NULL DEFAULT 0,
  `words_reviewed` INT NOT NULL DEFAULT 0,
  `conversations_completed` INT NOT NULL DEFAULT 0,
  `speaking_minutes` INT NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_user_activity_date` (`user_id`, `activity_date`),
  CONSTRAINT `fk_daily_activity_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  INDEX `idx_daily_activity_user_date` (`user_id`, `activity_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. Pronunciation Assessments table
CREATE TABLE IF NOT EXISTS `pronunciation_assessments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `vocabulary_id` INT NULL,
  `target_text` TEXT NOT NULL,
  `recognized_text` TEXT NOT NULL,
  `assessment_method` VARCHAR(100) NOT NULL DEFAULT 'transcript_comparison',
  `feedback_json` JSON NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_pron_assess_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pron_assess_vocab` FOREIGN KEY (`vocabulary_id`) REFERENCES `vocabulary` (`id`) ON DELETE SET NULL,
  INDEX `idx_pron_assess_user_time` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
