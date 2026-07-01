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

-- Assign student to counselor (only insert if not exists)
SET @counselor_id = (SELECT id FROM counselors WHERE user_id = @counselor_user_id);
SET @student_id = (SELECT id FROM students WHERE user_id = @student_user_id);
INSERT IGNORE INTO counselor_assignments (student_id, counselor_id, assignment_date, reason_for_assignment)
VALUES (@student_id, @counselor_id, CURDATE(), 'Initial assignment');

-- Create sample appointment (only insert if not exists)
INSERT IGNORE INTO appointments (student_id, counselor_id, appointment_date, duration_minutes, status)
VALUES (@student_id, @counselor_id, DATE_ADD(NOW(), INTERVAL 2 DAY), 60, 'scheduled');

-- Create sample survey summary for testing (only insert if not exists)
INSERT IGNORE INTO survey_summary (student_id, risk_level, overall_score, survey_completion_date)
VALUES (@student_id, 'Medium', 5, CURDATE());