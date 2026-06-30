-- Admin account (only insert if not exists)
INSERT IGNORE INTO users (name, email, password_hash, role, is_active)
VALUES ('System Admin', 'admin@example.com', 'admin123', 'admin', TRUE);

-- Counselor account (only insert if not exists)
INSERT IGNORE INTO users (name, email, password_hash, role, is_active)
VALUES ('Dr. Sarah Johnson', 'counselor@example.com', 'counselor123', 'counselor', TRUE);
SET @counselor_user_id = (SELECT id FROM users WHERE email = 'counselor@example.com');

-- Student account (only insert if not exists)
INSERT IGNORE INTO users (name, email, password_hash, role, is_active)
VALUES ('Alex Student', 'student@example.com', 'student123', 'student', TRUE);
SET @student_user_id = (SELECT id FROM users WHERE email = 'student@example.com');

-- Counselor profile (only insert if counselor doesn't exist)
INSERT IGNORE INTO counselors (user_id, license_number, specialization, bio, credentials, max_clients, current_client_count, is_available)
VALUES (@counselor_user_id, 'LIC-001', 'Clinical Psychology', 'Licensed counselor specializing in student mental health', 'PhD Clinical Psychology, 10 years experience', 25, 0, TRUE);

-- Student profile (only insert if student doesn't exist)
INSERT IGNORE INTO students (user_id, student_id_number, major, year, is_at_risk)
VALUES (@student_user_id, 'STU-2024-001', 'Computer Science', 'Sophomore', FALSE);