-- ============================================================
-- HMS Database Setup Script
-- Run this BEFORE python manage.py migrate
-- ============================================================

-- Create the database with UTF-8 charset
CREATE DATABASE IF NOT EXISTS hms_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create a dedicated application user (optional but recommended for production)
-- Replace 'hms_user' and 'strong_password' with your actual credentials
-- CREATE USER IF NOT EXISTS 'hms_user'@'localhost' IDENTIFIED BY 'strong_password';
-- GRANT ALL PRIVILEGES ON hms_db.* TO 'hms_user'@'localhost';
-- FLUSH PRIVILEGES;

USE hms_db;

-- ============================================================
-- The following tables are created automatically by Django migrations.
-- This script shows their structure for reference.
-- ============================================================

-- users table (created by accounts/migrations/0001_initial.py)
-- CREATE TABLE users (
--     id BIGINT AUTO_INCREMENT PRIMARY KEY,
--     password VARCHAR(128) NOT NULL,
--     last_login DATETIME(6) NULL,
--     is_superuser TINYINT(1) NOT NULL DEFAULT 0,
--     email VARCHAR(254) NOT NULL UNIQUE,
--     first_name VARCHAR(150) NOT NULL,
--     last_name VARCHAR(150) NOT NULL,
--     role VARCHAR(10) NOT NULL,
--     is_active TINYINT(1) NOT NULL DEFAULT 1,
--     is_staff TINYINT(1) NOT NULL DEFAULT 0,
--     date_joined DATETIME(6) NOT NULL,
--     updated_at DATETIME(6) NOT NULL
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Sample seed data (for local development / demo)
-- Note: Passwords are Django-hashed PBKDF2. Use manage.py to create real users.
-- ============================================================

-- To insert a superuser for admin panel, use:
--   python manage.py createsuperuser

-- Sample verification query — check tables after migration:
-- SHOW TABLES;
-- DESCRIBE users;
-- DESCRIBE doctors;
-- DESCRIBE patients;
-- DESCRIBE doctor_availability;
-- DESCRIBE appointments;
-- DESCRIBE google_oauth2_credentials;
