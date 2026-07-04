-- ============================================================================
-- Student Mental Health Resource Decision Support System - Database Schema
-- ============================================================================
-- This schema implements a complete DSS database with user management,
-- survey tracking, appointment scheduling, and decision logging.
-- ============================================================================

-- Drop existing objects if they exist (for safe re-initialization)
DROP TABLE IF EXISTS dss_logs;
DROP TABLE IF EXISTS counselor_notes;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS counselor_assignments;
DROP TABLE IF EXISTS survey_summary;
DROP TABLE IF EXISTS survey_responses;
DROP TABLE IF EXISTS survey_questions;
DROP TABLE IF EXISTS counselors;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

-- ============================================================================
-- USERS TABLE - Core user authentication and role management
-- ============================================================================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'counselor', 'admin') NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- STUDENTS TABLE - Student-specific information
-- ============================================================================
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    student_id_number VARCHAR(50) UNIQUE NOT NULL,
    major VARCHAR(100),
    year ENUM('Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate') NOT NULL DEFAULT 'Freshman',
    date_of_birth DATE,
    phone VARCHAR(20),
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    is_at_risk BOOLEAN DEFAULT FALSE,
    assigned_counselor_id INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_counselor_id) REFERENCES counselors(id) ON DELETE SET NULL,
    INDEX idx_student_id_number (student_id_number),
    INDEX idx_year (year),
    INDEX idx_is_at_risk (is_at_risk),
    INDEX idx_assigned_counselor_id (assigned_counselor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- COUNSELORS TABLE - Counselor-specific information and credentials
-- ============================================================================
CREATE TABLE counselors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    license_number VARCHAR(100) UNIQUE,
    specialization VARCHAR(255),
    bio TEXT,
    credentials TEXT,
    max_clients INT DEFAULT 20,
    current_client_count INT DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_is_available (is_available),
    INDEX idx_specialization (specialization)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SURVEY QUESTIONS TABLE - Defines all survey questions for DSS assessment
-- ============================================================================
CREATE TABLE survey_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice', 'scale', 'yes_no', 'text', 'numeric') NOT NULL,
    risk_weight DECIMAL(5, 2) DEFAULT 1.0,
    min_score INT,
    max_score INT,
    help_text TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_is_active (is_active),
    INDEX idx_display_order (display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SURVEY RESPONSES TABLE - Tracks individual survey responses from students
-- ============================================================================
CREATE TABLE survey_responses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    question_id INT NOT NULL,
    response_value VARCHAR(500),
    response_score DECIMAL(10, 2),
    response_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    survey_session_id VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES survey_questions(id) ON DELETE RESTRICT,
    INDEX idx_student_id (student_id),
    INDEX idx_question_id (question_id),
    INDEX idx_response_date (response_date),
    INDEX idx_survey_session_id (survey_session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SURVEY SUMMARY TABLE - DSS-computed results and risk assessment
-- ============================================================================
CREATE TABLE survey_summary (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL UNIQUE,
    risk_level ENUM('Low', 'Medium', 'High') NOT NULL DEFAULT 'Low',
    overall_score DECIMAL(10, 2),
    mental_health_score DECIMAL(10, 2),
    emotional_wellbeing_score DECIMAL(10, 2),
    substance_abuse_risk DECIMAL(10, 2),
    academic_stress_score DECIMAL(10, 2),
    social_isolation_score DECIMAL(10, 2),
    suicidal_ideation_indicator BOOLEAN DEFAULT FALSE,
    priority ENUM('Low', 'Medium', 'Critical') DEFAULT 'Low',
    recommendations TEXT,
    action_required BOOLEAN DEFAULT FALSE,
    survey_completion_date DATE NOT NULL,
    last_assessment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_risk_level (risk_level),
    INDEX idx_last_assessment_date (last_assessment_date),
    INDEX idx_action_required (action_required)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- APPOINTMENTS TABLE - Tracks counselor appointments with students
-- ============================================================================
CREATE TABLE appointments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    counselor_id INT NULL,
    appointment_date DATETIME NOT NULL,
    duration_minutes INT DEFAULT 60,
    status ENUM('scheduled', 'completed', 'cancelled', 'no_show', 'rescheduled') NOT NULL DEFAULT 'scheduled',
    appointment_type ENUM('initial', 'follow_up', 'emergency', 'group') DEFAULT 'follow_up',
    location VARCHAR(255),
    meeting_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (counselor_id) REFERENCES counselors(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_counselor_id (counselor_id),
    INDEX idx_appointment_date (appointment_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- COUNSELOR ASSIGNMENTS TABLE - Links students to assigned counselors
-- ============================================================================
CREATE TABLE counselor_assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    counselor_id INT NOT NULL,
    assignment_date DATE NOT NULL,
    status ENUM('active', 'inactive', 'transferred', 'completed') NOT NULL DEFAULT 'active',
    reason_for_assignment VARCHAR(255),
    transferred_to_counselor_id INT,
    transfer_reason VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (counselor_id) REFERENCES counselors(id) ON DELETE RESTRICT,
    FOREIGN KEY (transferred_to_counselor_id) REFERENCES counselors(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_counselor_id (counselor_id),
    INDEX idx_status (status),
    UNIQUE KEY unique_active_assignment (student_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- COUNSELOR NOTES TABLE - Session notes and observations from counselors
-- ============================================================================
CREATE TABLE counselor_notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    appointment_id INT NOT NULL,
    student_id INT NOT NULL,
    counselor_id INT NOT NULL,
    note_content TEXT NOT NULL,
    session_summary TEXT,
    mood_observed VARCHAR(100),
    mental_status_assessment TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_plan TEXT,
    recommended_resources TEXT,
    risk_assessment_update ENUM('Low', 'Medium', 'High'),
    referral_needed BOOLEAN DEFAULT FALSE,
    referral_details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (counselor_id) REFERENCES counselors(id) ON DELETE RESTRICT,
    INDEX idx_student_id (student_id),
    INDEX idx_counselor_id (counselor_id),
    INDEX idx_appointment_id (appointment_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DSS LOGS TABLE - Decision Support System action and outcome tracking
-- ============================================================================
CREATE TABLE dss_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    decision_type VARCHAR(100) NOT NULL,
    decision_trigger VARCHAR(255),
    input_data JSON,
    risk_level_determined ENUM('Low', 'Medium', 'High') NOT NULL,
    confidence_score DECIMAL(5, 2),
    recommendation_type VARCHAR(100),
    recommended_action TEXT,
    action_taken VARCHAR(255),
    action_taken_by_user_id INT,
    action_timestamp TIMESTAMP NULL,
    outcome VARCHAR(255),
    follow_up_status ENUM('pending', 'in_progress', 'completed', 'escalated') DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (action_taken_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_decision_type (decision_type),
    INDEX idx_risk_level_determined (risk_level_determined),
    INDEX idx_created_at (created_at),
    INDEX idx_follow_up_status (follow_up_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- AUDIT TABLE - Track system actions for compliance and debugging
-- ============================================================================
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_entity_type (entity_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- VIEWS - For simplified data access patterns
-- ============================================================================

-- View: Active Students with their assigned counselors
CREATE VIEW v_active_students_with_counselors AS
SELECT 
    s.id AS student_id,
    u.id AS user_id,
    u.name AS student_name,
    u.email AS student_email,
    s.student_id_number,
    s.major,
    s.year,
    ss.risk_level,
    s.assigned_counselor_id AS counselor_id,
    cu.name AS counselor_name
FROM students s
JOIN users u ON s.user_id = u.id
LEFT JOIN survey_summary ss ON s.id = ss.student_id
LEFT JOIN counselors c ON s.assigned_counselor_id = c.id
LEFT JOIN users cu ON c.user_id = cu.id
WHERE u.is_active = TRUE;

-- View: High-Risk Students requiring immediate attention
CREATE VIEW v_high_risk_students AS
SELECT 
    s.id AS student_id,
    u.name AS student_name,
    u.email,
    s.student_id_number,
    ss.risk_level,
    ss.overall_score,
    ss.suicidal_ideation_indicator,
    ss.last_assessment_date,
    s.assigned_counselor_id AS counselor_id,
    cu.name AS assigned_counselor
FROM students s
JOIN users u ON s.user_id = u.id
JOIN survey_summary ss ON s.id = ss.student_id
LEFT JOIN counselors c ON s.assigned_counselor_id = c.id
LEFT JOIN users cu ON c.user_id = cu.id
WHERE ss.risk_level = 'High' AND u.is_active = TRUE;

-- View: Counselor Workload Summary
CREATE VIEW v_counselor_workload AS
SELECT 
    c.id AS counselor_id,
    cu.name AS counselor_name,
    cu.email,
    c.current_client_count,
    c.max_clients,
    COUNT(DISTINCT ca.student_id) AS active_assignments,
    COUNT(DISTINCT a.id) AS scheduled_appointments,
    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) AS completed_appointments
FROM counselors c
JOIN users cu ON c.user_id = cu.id
LEFT JOIN counselor_assignments ca ON c.id = ca.counselor_id AND ca.status = 'active'
LEFT JOIN appointments a ON c.id = a.counselor_id AND a.appointment_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY c.id, cu.name, cu.email, c.current_client_count, c.max_clients;

-- ============================================================================
-- STORED PROCEDURES - For complex operations
-- ============================================================================

-- Procedure: Calculate risk level based on survey responses
DELIMITER //
CREATE PROCEDURE calculate_student_risk_level(IN p_student_id INT)
BEGIN
    DECLARE v_overall_score DECIMAL(10, 2);
    DECLARE v_mental_health_score DECIMAL(10, 2);
    DECLARE v_substance_abuse_risk DECIMAL(10, 2);
    DECLARE v_academic_stress_score DECIMAL(10, 2);
    DECLARE v_risk_level VARCHAR(20);
    DECLARE v_suicidal_indicator BOOLEAN;
    
    -- Calculate category scores
    SELECT COALESCE(AVG(sr.response_score), 0) INTO v_mental_health_score
    FROM survey_responses sr
    JOIN survey_questions sq ON sr.question_id = sq.id
    WHERE sr.student_id = p_student_id
    AND sq.category = 'mental_health'
    AND sr.response_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    SELECT COALESCE(AVG(sr.response_score), 0) INTO v_substance_abuse_risk
    FROM survey_responses sr
    JOIN survey_questions sq ON sr.question_id = sq.id
    WHERE sr.student_id = p_student_id
    AND sq.category = 'substance_abuse'
    AND sr.response_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    SELECT COALESCE(AVG(sr.response_score), 0) INTO v_academic_stress_score
    FROM survey_responses sr
    JOIN survey_questions sq ON sr.question_id = sq.id
    WHERE sr.student_id = p_student_id
    AND sq.category = 'academic_stress'
    AND sr.response_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Calculate overall score
    SET v_overall_score = (v_mental_health_score * 0.4) + (v_substance_abuse_risk * 0.3) + (v_academic_stress_score * 0.3);
    
    -- Check for suicidal ideation (high score in specific questions)
    SELECT COUNT(*) > 0 INTO v_suicidal_indicator
    FROM survey_responses sr
    JOIN survey_questions sq ON sr.question_id = sq.id
    WHERE sr.student_id = p_student_id
    AND sq.category = 'suicidal_ideation'
    AND sr.response_score >= 8
    AND sr.response_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Determine risk level
    IF v_suicidal_indicator THEN
        SET v_risk_level = 'High';
    ELSEIF v_overall_score >= 7 THEN
        SET v_risk_level = 'High';
    ELSEIF v_overall_score >= 5 THEN
        SET v_risk_level = 'Medium';
    ELSE
        SET v_risk_level = 'Low';
    END IF;
    
    -- Update survey summary
    INSERT INTO survey_summary (
        student_id, risk_level, overall_score, mental_health_score,
        substance_abuse_risk, academic_stress_score, suicidal_ideation_indicator,
        survey_completion_date
    ) VALUES (
        p_student_id, v_risk_level, v_overall_score, v_mental_health_score,
        v_substance_abuse_risk, v_academic_stress_score, v_suicidal_indicator,
        CURDATE()
    )
    ON DUPLICATE KEY UPDATE
        risk_level = v_risk_level,
        overall_score = v_overall_score,
        mental_health_score = v_mental_health_score,
        substance_abuse_risk = v_substance_abuse_risk,
        academic_stress_score = v_academic_stress_score,
        suicidal_ideation_indicator = v_suicidal_indicator,
        last_assessment_date = CURRENT_TIMESTAMP;
    
END //
DELIMITER ;

-- Procedure: Assign counselor to student
DELIMITER //
CREATE PROCEDURE assign_counselor_to_student(
    IN p_student_id INT,
    IN p_counselor_id INT,
    IN p_reason VARCHAR(255)
)
BEGIN
    DECLARE v_current_count INT;
    DECLARE v_max_clients INT;
    
    -- Check if counselor has capacity
    SELECT c.current_client_count, c.max_clients INTO v_current_count, v_max_clients
    FROM counselors c
    WHERE c.id = p_counselor_id;
    
    IF v_current_count >= v_max_clients THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Counselor is at maximum capacity';
    END IF;
    
    -- Deactivate any existing assignment
    UPDATE counselor_assignments
    SET status = 'inactive'
    WHERE student_id = p_student_id AND status = 'active';
    
    -- Create new assignment
    INSERT INTO counselor_assignments (student_id, counselor_id, assignment_date, reason_for_assignment)
    VALUES (p_student_id, p_counselor_id, CURDATE(), p_reason);
    
    -- Update counselor client count
    UPDATE counselors
    SET current_client_count = current_client_count + 1
    WHERE id = p_counselor_id;
    
END //
DELIMITER ;

-- ============================================================================
-- SEED DATA - Initialize system with sample categories
-- ============================================================================

-- Insert survey question categories and base questions
INSERT INTO survey_questions (category, question_text, question_type, risk_weight, min_score, max_score, display_order, is_active)
VALUES
-- Mental Health Category
('mental_health', 'How often do you feel sad or depressed?', 'scale', 1.5, 1, 10, 1, TRUE),
('mental_health', 'Do you have difficulty concentrating on tasks?', 'scale', 1.2, 1, 10, 2, TRUE),
('mental_health', 'How often do you feel anxious or worried?', 'scale', 1.3, 1, 10, 3, TRUE),
('mental_health', 'Do you sleep well at night?', 'scale', 1.0, 1, 10, 4, TRUE),

-- Substance Abuse Category
('substance_abuse', 'How often do you consume alcohol?', 'scale', 1.4, 1, 10, 5, TRUE),
('substance_abuse', 'Have you ever used drugs (marijuana, cocaine, etc.)?', 'yes_no', 2.0, 0, 1, 6, TRUE),
('substance_abuse', 'Do you feel dependent on any substance?', 'yes_no', 2.5, 0, 1, 7, TRUE),

-- Academic Stress Category
('academic_stress', 'How stressful is your current academic workload?', 'scale', 1.2, 1, 10, 8, TRUE),
('academic_stress', 'Are you struggling with any subjects?', 'yes_no', 1.0, 0, 1, 9, TRUE),
('academic_stress', 'How often do you feel overwhelmed by assignments?', 'scale', 1.1, 1, 10, 10, TRUE),

-- Social Support Category
('social_support', 'Do you have friends or family you can talk to?', 'yes_no', 1.5, 0, 1, 11, TRUE),
('social_support', 'How often do you feel lonely or isolated?', 'scale', 1.3, 1, 10, 12, TRUE),

-- Suicidal Ideation Category (Critical)
('suicidal_ideation', 'Have you ever thought about harming yourself?', 'yes_no', 3.0, 0, 1, 13, TRUE),
('suicidal_ideation', 'Have you considered ending your life?', 'yes_no', 3.0, 0, 1, 14, TRUE);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
