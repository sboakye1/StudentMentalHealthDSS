# Database Schema - Quick Reference Guide

## Table Overview

| Table | Purpose | Key Fields | Relationships |
|-------|---------|-----------|---|
| **users** | Authentication & roles | id, email, role, is_active | Parent to students, counselors |
| **students** | Student profiles | id, user_id, student_id_number, year | 1:1 with users, 1:M with surveys |
| **counselors** | Counselor credentials | id, user_id, license_number, max_clients | 1:1 with users, 1:M with appointments |
| **survey_questions** | Survey templates | id, category, question_text, question_type | 1:M with responses |
| **survey_responses** | Student answers | id, student_id, question_id, response_score | M:1 with students & questions |
| **survey_summary** | DSS results (cached) | id, student_id, risk_level, overall_score | 1:1 with students |
| **appointments** | Scheduled sessions | id, student_id, counselor_id, appointment_date | M:1 with students & counselors |
| **counselor_assignments** | Student-counselor links | id, student_id, counselor_id, status | M:1 with students & counselors |
| **counselor_notes** | Session documentation | id, appointment_id, note_content | M:1 with appointments, students, counselors |
| **dss_logs** | Decision tracking | id, student_id, decision_type, risk_level_determined | M:1 with students & users |
| **audit_logs** | System audit trail | id, user_id, action, entity_type, entity_id | M:1 with users |

---

## Common SQL Queries

### User & Authentication

```sql
-- Get student user profile
SELECT u.*, s.student_id_number, s.year, s.major
FROM users u
JOIN students s ON u.id = s.user_id
WHERE u.email = ? AND u.is_active = TRUE;

-- Get counselor profile with workload
SELECT u.*, c.specialization, c.current_client_count, c.max_clients
FROM users u
JOIN counselors c ON u.id = c.user_id
WHERE u.email = ? AND c.is_available = TRUE;

-- List all active users by role
SELECT * FROM users WHERE is_active = TRUE AND role = 'student' ORDER BY name;
```

### Student Risk Assessment

```sql
-- Get student's latest risk assessment
SELECT * FROM survey_summary
WHERE student_id = ?
ORDER BY last_assessment_date DESC
LIMIT 1;

-- Find all high-risk students
SELECT * FROM v_high_risk_students
ORDER BY overall_score DESC;

-- Get student's survey history
SELECT sr.*, sq.category, sq.question_text
FROM survey_responses sr
JOIN survey_questions sq ON sr.question_id = sq.id
WHERE sr.student_id = ?
ORDER BY sr.response_date DESC;

-- Check if suicidal ideation flag triggered
SELECT * FROM survey_summary
WHERE student_id = ? AND suicidal_ideation_indicator = TRUE;
```

### Appointment Management

```sql
-- Get student's upcoming appointments
SELECT a.*, u.name AS counselor_name, u.email AS counselor_email
FROM appointments a
JOIN counselors c ON a.counselor_id = c.id
JOIN users u ON c.user_id = u.id
WHERE a.student_id = ? AND a.appointment_date > NOW() AND a.status = 'scheduled'
ORDER BY a.appointment_date ASC;

-- Get counselor's schedule for a specific date
SELECT a.*, u.name AS student_name, s.student_id_number
FROM appointments a
JOIN students s ON a.student_id = s.id
JOIN users u ON s.user_id = u.id
WHERE a.counselor_id = ? 
AND DATE(a.appointment_date) = ?
ORDER BY a.appointment_date ASC;

-- Check for appointment conflicts
SELECT * FROM appointments
WHERE counselor_id = ?
AND status IN ('scheduled', 'completed')
AND appointment_date BETWEEN ? AND DATE_ADD(?, INTERVAL ? MINUTE)
AND id != ?;
```

### Counselor Assignment

```sql
-- Get student's assigned counselor
SELECT c.*, u.name, u.email
FROM counselors c
JOIN counselor_assignments ca ON c.id = ca.counselor_id
JOIN users u ON c.user_id = u.id
WHERE ca.student_id = ? AND ca.status = 'active';

-- Get counselor's assigned students
SELECT s.*, u.name, u.email, ss.risk_level
FROM students s
JOIN users u ON s.user_id = u.id
JOIN counselor_assignments ca ON s.id = ca.student_id
LEFT JOIN survey_summary ss ON s.id = ss.student_id
WHERE ca.counselor_id = ? AND ca.status = 'active'
ORDER BY ss.risk_level DESC;

-- List available counselors sorted by specialization
SELECT c.*, u.name, u.email,
       (c.max_clients - c.current_client_count) AS available_slots
FROM counselors c
JOIN users u ON c.user_id = u.id
WHERE c.is_available = TRUE
ORDER BY available_slots DESC, c.specialization;
```

### DSS Decision Tracking

```sql
-- Get student's DSS decision history
SELECT * FROM dss_logs
WHERE student_id = ?
ORDER BY created_at DESC
LIMIT 20;

-- Find all pending follow-ups
SELECT dl.*, s.user_id, u.name
FROM dss_logs dl
JOIN students s ON dl.student_id = s.id
JOIN users u ON s.user_id = u.id
WHERE dl.follow_up_status = 'pending'
ORDER BY dl.created_at ASC;

-- Get DSS effectiveness metrics
SELECT decision_type, 
       COUNT(*) AS total_decisions,
       SUM(CASE WHEN outcome = 'completed' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN outcome = 'escalated' THEN 1 ELSE 0 END) AS escalated,
       ROUND(SUM(confidence_score) / COUNT(*), 2) AS avg_confidence
FROM dss_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY decision_type;
```

### Counselor Notes

```sql
-- Get session notes for a student
SELECT cn.*, a.appointment_date, c_user.name AS counselor_name
FROM counselor_notes cn
JOIN appointments a ON cn.appointment_id = a.id
JOIN counselors c ON cn.counselor_id = c.id
JOIN users c_user ON c.user_id = c_user.id
WHERE cn.student_id = ?
ORDER BY a.appointment_date DESC;

-- Find notes requiring follow-up
SELECT cn.*, s.user_id, u.name
FROM counselor_notes cn
JOIN students s ON cn.student_id = s.id
JOIN users u ON s.user_id = u.id
WHERE cn.follow_up_required = TRUE
ORDER BY cn.created_at ASC;

-- Get referral tracking
SELECT cn.*, u.name, s.student_id_number
FROM counselor_notes cn
JOIN students s ON cn.student_id = s.id
JOIN users u ON s.user_id = u.id
WHERE cn.referral_needed = TRUE
ORDER BY cn.created_at DESC;
```

### Audit & Compliance

```sql
-- Get audit trail for a user's actions
SELECT * FROM audit_logs
WHERE user_id = ?
ORDER BY created_at DESC
LIMIT 100;

-- Track changes to a specific entity
SELECT * FROM audit_logs
WHERE entity_type = ? AND entity_id = ?
ORDER BY created_at DESC;

-- Get all sensitive data access
SELECT * FROM audit_logs
WHERE action = 'VIEW' AND entity_type IN ('survey_responses', 'counselor_notes')
ORDER BY created_at DESC
LIMIT 50;

-- Compliance report: All changes to user roles
SELECT al.*, u.name AS user_making_change
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
WHERE al.entity_type = 'users' AND al.action = 'UPDATE'
AND al.new_values LIKE '%"role"%'
ORDER BY al.created_at DESC;
```

---

## Risk Level Classification

```
Low Risk:
  - overall_score < 5
  - No suicidal ideation
  - Stable academic performance

Medium Risk:
  - overall_score 5-7
  - Some emotional concerns
  - Substance use exploration

High Risk:
  - overall_score ≥ 7
  - OR suicidal_ideation_indicator = TRUE
  - Requires immediate intervention
```

---

## Appointment Status Flow

```
scheduled → completed → (counselor_notes created)
         → cancelled
         → no_show
         → rescheduled
```

---

## Assignment Status Flow

```
active → inactive (manual deactivation)
      → transferred (moved to different counselor)
      → completed (student terminated)
```

---

## DSS Follow-up Status Flow

```
pending → in_progress (action initiated)
       → completed (resolution achieved)
       → escalated (crisis intervention)
```

---

## Database Functions (Stored Procedures)

### calculate_student_risk_level(student_id INT)
Recalculates risk level from recent survey responses and updates SURVEY_SUMMARY.

```sql
CALL calculate_student_risk_level(123);
```

### assign_counselor_to_student(student_id INT, counselor_id INT, reason VARCHAR)
Safely assigns student to counselor with capacity validation.

```sql
CALL assign_counselor_to_student(123, 45, 'High-risk assessment follow-up');
```

---

## Performance Considerations

### High-Volume Queries (Cache Results)
- `v_high_risk_students` (accessed by dashboard)
- Recent survey summaries
- Counselor workload view

### Query Optimization Tips
1. Always use indexes: email, student_id_number, risk_level, appointment_date
2. Use LIMIT for large result sets
3. Avoid SELECT * unless necessary
4. Pre-aggregate using views or materialized snapshots
5. Archive old records (>2 years) to separate history table

### Slow Query Prevention
```sql
-- Add this index if appointment queries slow down
CREATE INDEX idx_appointment_student_status 
ON appointments(student_id, status, appointment_date);

-- For survey analytics
CREATE INDEX idx_response_category_date 
ON survey_responses(question_id, response_date);
```

---

## Data Retention Policy

- **Active Records**: Full transaction logging indefinitely
- **Completed Appointments**: Retain 7 years (regulatory requirement)
- **Survey Responses**: Archive after 3 years to history table
- **Audit Logs**: Retain 5 years minimum (compliance)
- **DSS Logs**: Permanent (algorithm validation)

---

## Backup & Recovery

```bash
# Daily incremental backup
mysqldump --routines -u root -p student_mental_health_dss | gzip > backup_$(date +%s).sql.gz

# Full recovery
gunzip < backup_xxx.sql.gz | mysql -u root -p student_mental_health_dss

# Point-in-time recovery (if binary logging enabled)
mysqlbinlog --start-datetime='2024-01-01 00:00:00' --stop-datetime='2024-01-01 10:00:00' \
  /var/log/mysql/mysql-bin.000001 | mysql -u root -p
```

---

## Connection String Examples

### Python (mysql-connector)
```python
import mysql.connector
config = {
    'host': 'localhost',
    'user': 'app_user',
    'password': 'secure_password',
    'database': 'student_mental_health_dss',
    'charset': 'utf8mb4',
}
conn = mysql.connector.connect(**config)
```

### Connection Pool (Production)
```python
pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="dss_pool",
    pool_size=5,
    pool_reset_session=True,
    **config
)
```

---

*Quick Reference v1.0 | 2026-06-28*
