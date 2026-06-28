# Student Mental Health DSS - Database Schema Documentation

## Overview
This document describes the complete MySQL database schema for the Student Mental Health Decision Support System (DSS). The schema is designed to support user management, survey administration, appointment scheduling, and decision tracking for mental health resource allocation.

---

## Table of Contents
1. [Database Design Principles](#database-design-principles)
2. [Table Descriptions](#table-descriptions)
3. [Relationships & Constraints](#relationships--constraints)
4. [Entity-Relationship Diagram](#entity-relationship-diagram)
5. [Indexes for Performance](#indexes-for-performance)
6. [Views](#views)
7. [Stored Procedures](#stored-procedures)
8. [Normalization Analysis](#normalization-analysis)
9. [Implementation Guide](#implementation-guide)

---

## Database Design Principles

### Core Design Goals
- **3NF Normalization**: All tables designed to eliminate data redundancy
- **Referential Integrity**: Foreign keys with appropriate cascading rules
- **Audit Trail**: Timestamps on all records for tracking changes
- **Performance**: Strategic indexing on frequently queried columns
- **Extensibility**: Room for future features without schema redesign

### Key Design Decisions

#### Role-Based Access (Users Table)
- Single `users` table with ENUM role instead of separate admin/staff tables
- Reduces complexity while maintaining role-based logic
- Future roles easily added to ENUM (e.g., 'staff', 'parent')

#### Survey System Design
- Separation of `survey_questions` (templates) from `survey_responses` (data)
- Allows for adaptive surveys without historical data corruption
- `survey_summary` caches DSS calculation results for performance

#### Risk Assessment
- ENUM field for risk levels: 'Low', 'Medium', 'High'
- Calculated via stored procedure from survey responses
- Supports both binary flags (suicidal_ideation_indicator) and scored categories

#### Decision Tracking
- `dss_logs` table tracks every decision and its outcome
- JSON storage for flexible decision metadata
- Follow-up status for accountability and compliance

---

## Table Descriptions

### 1. USERS Table
**Purpose**: Core authentication and user management

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique user identifier |
| name | VARCHAR(255) | NOT NULL | User's full name |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email for authentication/notifications |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt or Argon2 hash (never plain text) |
| role | ENUM | DEFAULT 'student' | Defines user type: student, counselor, admin |
| is_active | BOOLEAN | DEFAULT TRUE | Soft delete for compliance |
| last_login | TIMESTAMP | NULL | For activity monitoring |
| created_at | TIMESTAMP | AUTO | Account creation timestamp |
| updated_at | TIMESTAMP | AUTO | Last modification timestamp |

**Indexes**:
- `idx_email`: Fast login and lookup
- `idx_role`: Filter users by role
- `idx_is_active`: Quick retrieval of active users only

**Notes**:
- Email field is UNIQUE to prevent duplicate accounts
- password_hash must be hashed with strong algorithm (bcrypt, Argon2)
- is_active allows soft-delete for audit compliance
- last_login tracks user engagement

---

### 2. STUDENTS Table
**Purpose**: Student-specific profile information

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique student identifier |
| user_id | INT | FOREIGN KEY, UNIQUE | Links to users table |
| student_id_number | VARCHAR(50) | UNIQUE | University ID number |
| major | VARCHAR(100) | NULL | Field of study |
| year | ENUM | DEFAULT 'Freshman' | Academic year classification |
| date_of_birth | DATE | NULL | For age-based interventions |
| phone | VARCHAR(20) | NULL | Contact information |
| emergency_contact_name | VARCHAR(255) | NULL | Emergency contact person |
| emergency_contact_phone | VARCHAR(20) | NULL | Emergency contact number |
| is_at_risk | BOOLEAN | DEFAULT FALSE | Quick flag for at-risk students |
| created_at | TIMESTAMP | AUTO | Registration timestamp |
| updated_at | TIMESTAMP | AUTO | Last update timestamp |

**Relationships**:
- 1:1 relationship with `users` table
- 1:Many with `survey_responses`
- 1:Many with `appointments`
- 1:1 with `survey_summary`

**Indexes**:
- `idx_student_id_number`: University system integration
- `idx_year`: Cohort analysis
- `idx_is_at_risk`: Quick identification of high-risk students

**Notes**:
- UNIQUE on user_id ensures each student maps to exactly one user
- is_at_risk is a cache of survey_summary.risk_level for quick filtering
- Emergency contact fields support crisis response

---

### 3. COUNSELORS Table
**Purpose**: Counselor credentials and availability management

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique counselor identifier |
| user_id | INT | FOREIGN KEY, UNIQUE | Links to users table |
| license_number | VARCHAR(100) | UNIQUE, NULL | Professional license |
| specialization | VARCHAR(255) | NULL | Area of expertise |
| bio | TEXT | NULL | Professional biography |
| credentials | TEXT | NULL | Educational background |
| max_clients | INT | DEFAULT 20 | Capacity limit |
| current_client_count | INT | DEFAULT 0 | Current active clients |
| is_available | BOOLEAN | DEFAULT TRUE | Availability status |
| created_at | TIMESTAMP | AUTO | Onboarding timestamp |
| updated_at | TIMESTAMP | AUTO | Last update timestamp |

**Relationships**:
- 1:1 relationship with `users` table
- 1:Many with `appointments`
- 1:Many with `counselor_assignments`
- 1:Many with `counselor_notes`

**Indexes**:
- `idx_is_available`: Filter available counselors
- `idx_specialization`: Match students to counselor expertise

**Notes**:
- current_client_count must be maintained via triggers or app logic
- max_clients enforces workload management
- License number enables professional verification

---

### 4. SURVEY_QUESTIONS Table
**Purpose**: Master list of assessment questions for DSS surveys

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique question identifier |
| category | VARCHAR(100) | NOT NULL | Question domain (mental_health, substance_abuse, etc.) |
| question_text | TEXT | NOT NULL | The actual question presented to student |
| question_type | ENUM | NOT NULL | Response format: scale, yes_no, multiple_choice, numeric, text |
| risk_weight | DECIMAL(5,2) | DEFAULT 1.0 | Weight in DSS calculation (e.g., 2.5 for critical questions) |
| min_score | INT | NULL | Minimum possible score |
| max_score | INT | NULL | Maximum possible score |
| help_text | TEXT | NULL | Additional context for students |
| is_active | BOOLEAN | DEFAULT TRUE | Soft delete for inactive questions |
| display_order | INT | NULL | Presentation sequence |
| created_at | TIMESTAMP | AUTO | Question creation timestamp |
| updated_at | TIMESTAMP | AUTO | Question modification timestamp |

**Relationships**:
- 1:Many with `survey_responses`

**Indexes**:
- `idx_category`: Group questions by domain
- `idx_is_active`: Retrieve only active questions
- `idx_display_order`: Maintain question order

**Categories**:
- `mental_health`: Depression, anxiety, mood
- `substance_abuse`: Alcohol, drugs, dependency
- `academic_stress`: Coursework, performance, workload
- `social_support`: Relationships, isolation, support systems
- `suicidal_ideation`: Self-harm thoughts (CRITICAL)

**Notes**:
- risk_weight (e.g., 3.0 for suicidal questions) impacts DSS calculations
- question_type allows flexible response collection
- Soft delete (is_active) preserves historical survey data

---

### 5. SURVEY_RESPONSES Table
**Purpose**: Individual student responses to survey questions

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique response identifier |
| student_id | INT | FOREIGN KEY | Links to student |
| question_id | INT | FOREIGN KEY | Links to survey question |
| response_value | VARCHAR(500) | NULL | Raw response (text, choice, etc.) |
| response_score | DECIMAL(10,2) | NULL | Numeric score assigned |
| response_date | TIMESTAMP | DEFAULT NOW() | When response was recorded |
| survey_session_id | VARCHAR(100) | NULL | Groups responses from same survey session |
| created_at | TIMESTAMP | AUTO | Record creation timestamp |

**Relationships**:
- N:1 with `students`
- N:1 with `survey_questions`

**Indexes**:
- `idx_student_id`: Query student's responses
- `idx_question_id`: Analyze responses to specific question
- `idx_response_date`: Time-based analysis
- `idx_survey_session_id`: Group survey sessions

**Notes**:
- response_score is calculated from response_value based on question_type
- survey_session_id groups responses from same survey administration
- response_date tracks when student answered (important for time-based analysis)
- ON DELETE CASCADE: Removing student removes all responses

---

### 6. SURVEY_SUMMARY Table
**Purpose**: Cached DSS calculation results for each student

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique summary identifier |
| student_id | INT | FOREIGN KEY, UNIQUE | One summary per student |
| risk_level | ENUM | NOT NULL, DEFAULT 'Low' | Computed risk: Low, Medium, High |
| overall_score | DECIMAL(10,2) | NULL | Weighted aggregate score |
| mental_health_score | DECIMAL(10,2) | NULL | Mental health category score |
| emotional_wellbeing_score | DECIMAL(10,2) | NULL | Emotional stability score |
| substance_abuse_risk | DECIMAL(10,2) | NULL | Substance use risk score |
| academic_stress_score | DECIMAL(10,2) | NULL | Academic pressure score |
| social_isolation_score | DECIMAL(10,2) | NULL | Social support score |
| suicidal_ideation_indicator | BOOLEAN | DEFAULT FALSE | Critical risk flag |
| recommendations | TEXT | NULL | DSS-generated recommendations |
| action_required | BOOLEAN | DEFAULT FALSE | Requires immediate counselor action |
| survey_completion_date | DATE | NOT NULL | When survey was completed |
| last_assessment_date | TIMESTAMP | NOT NULL | Last DSS calculation |
| created_at | TIMESTAMP | AUTO | First assessment timestamp |
| updated_at | TIMESTAMP | AUTO | Last update timestamp |

**Relationships**:
- 1:1 relationship with `students` table

**Indexes**:
- `idx_risk_level`: Filter by risk classification
- `idx_last_assessment_date`: Identify stale assessments
- `idx_action_required`: Priority queue for counselor action

**Calculation Logic** (via `calculate_student_risk_level` stored procedure):
```
overall_score = (mental_health_score × 0.4) + (substance_abuse_risk × 0.3) + (academic_stress_score × 0.3)

risk_level determination:
  IF suicidal_ideation_indicator = TRUE → High
  ELSE IF overall_score ≥ 7 → High
  ELSE IF overall_score ≥ 5 → Medium
  ELSE → Low
```

**Notes**:
- UNIQUE on student_id: Only one active summary per student
- Scores normalized to 0-10 scale
- suicidal_ideation_indicator is CRITICAL - triggers immediate escalation
- action_required flags students needing counselor followup

---

### 7. APPOINTMENTS Table
**Purpose**: Schedule and track counselor-student meetings

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique appointment identifier |
| student_id | INT | FOREIGN KEY | Links to student |
| counselor_id | INT | FOREIGN KEY | Links to assigned counselor |
| appointment_date | DATETIME | NOT NULL | Date/time of appointment |
| duration_minutes | INT | DEFAULT 60 | Session length |
| status | ENUM | NOT NULL, DEFAULT 'scheduled' | State: scheduled, completed, cancelled, no_show, rescheduled |
| appointment_type | ENUM | DEFAULT 'follow_up' | Type: initial, follow_up, emergency, group |
| location | VARCHAR(255) | NULL | Physical location or Zoom link |
| meeting_notes | TEXT | NULL | Brief notes from meeting |
| created_at | TIMESTAMP | AUTO | Appointment creation timestamp |
| updated_at | TIMESTAMP | AUTO | Last modification timestamp |

**Relationships**:
- N:1 with `students`
- N:1 with `counselors`
- 1:1 with `counselor_notes`

**Indexes**:
- `idx_student_id`: View student's appointments
- `idx_counselor_id`: View counselor's schedule
- `idx_appointment_date`: Upcoming appointments
- `idx_status`: Filter by state

**Statuses**:
- `scheduled`: Future appointment
- `completed`: Finished session
- `cancelled`: Student/counselor cancellation
- `no_show`: Student didn't attend
- `rescheduled`: Appointment moved to different date

**Notes**:
- appointment_date should be checked for conflicts during booking
- Emergency appointments bypass normal scheduling
- Location supports hybrid (in-person + virtual) delivery

---

### 8. COUNSELOR_ASSIGNMENTS Table
**Purpose**: Track which students are assigned to which counselors

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique assignment identifier |
| student_id | INT | FOREIGN KEY | Student being assigned |
| counselor_id | INT | FOREIGN KEY | Assigned counselor |
| assignment_date | DATE | NOT NULL | When assignment was made |
| status | ENUM | NOT NULL, DEFAULT 'active' | State: active, inactive, transferred, completed |
| reason_for_assignment | VARCHAR(255) | NULL | Why this assignment (e.g., "High-risk follow-up") |
| transferred_to_counselor_id | INT | FOREIGN KEY, NULL | If transferred, new counselor |
| transfer_reason | VARCHAR(255) | NULL | Why transfer occurred |
| created_at | TIMESTAMP | AUTO | Assignment creation timestamp |
| updated_at | TIMESTAMP | AUTO | Last modification timestamp |

**Relationships**:
- N:1 with `students`
- N:1 with `counselors`
- Self-referencing foreign key to `counselors` for transfers

**Constraints**:
- UNIQUE KEY on (student_id, status='active') ensures only one active assignment per student
- ON DELETE RESTRICT on counselor_id prevents deletion while assigned

**Indexes**:
- `idx_student_id`: Find student's assignments
- `idx_counselor_id`: Find counselor's assignments
- `idx_status`: Filter by assignment state

**Notes**:
- Supports transfer tracking for audit trail
- Allows reassignment without losing assignment history
- Active vs. inactive enables historical queries

---

### 9. COUNSELOR_NOTES Table
**Purpose**: Document session observations and treatment progress

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique note identifier |
| appointment_id | INT | FOREIGN KEY | Links to specific appointment |
| student_id | INT | FOREIGN KEY | Denormalized for query optimization |
| counselor_id | INT | FOREIGN KEY | Note author |
| note_content | TEXT | NOT NULL | Detailed session notes |
| session_summary | TEXT | NULL | Brief summary of session |
| mood_observed | VARCHAR(100) | NULL | Client's mood (depressed, anxious, calm, etc.) |
| mental_status_assessment | TEXT | NULL | Clinical observations |
| follow_up_required | BOOLEAN | DEFAULT FALSE | Needs follow-up session |
| follow_up_plan | TEXT | NULL | Specific follow-up actions |
| recommended_resources | TEXT | NULL | Resources shared (books, websites, services) |
| risk_assessment_update | ENUM | NULL | Risk level change: Low, Medium, High |
| referral_needed | BOOLEAN | DEFAULT FALSE | Needs referral to specialist |
| referral_details | TEXT | NULL | Referral destination and reason |
| created_at | TIMESTAMP | AUTO | Note creation timestamp |
| updated_at | TIMESTAMP | AUTO | Last modification timestamp |

**Relationships**:
- N:1 with `appointments`
- N:1 with `students`
- N:1 with `counselors`

**Indexes**:
- `idx_student_id`: View student's counseling history
- `idx_counselor_id`: View counselor's notes
- `idx_appointment_id`: Link to specific session
- `idx_created_at`: Recent notes

**Notes**:
- Denormalized student_id and counselor_id for faster queries
- ON DELETE CASCADE on appointment allows note archival
- Supports clinical documentation requirements
- HIPAA compliance: These notes are sensitive data

---

### 10. DSS_LOGS Table
**Purpose**: Track all DSS decisions and their outcomes

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique log entry identifier |
| student_id | INT | FOREIGN KEY | Student this decision involves |
| decision_type | VARCHAR(100) | NOT NULL | Type of decision (risk_assessment, appointment_recommendation, referral_suggestion, intervention_level) |
| decision_trigger | VARCHAR(255) | NULL | What triggered decision (survey_completion, no_show, escalation, etc.) |
| input_data | JSON | NULL | Raw input to DSS algorithm |
| risk_level_determined | ENUM | NOT NULL | Result: Low, Medium, High |
| confidence_score | DECIMAL(5,2) | NULL | How confident (0-1.0) in decision |
| recommendation_type | VARCHAR(100) | NULL | Type: routine_counseling, urgent_appointment, specialist_referral, emergency_protocol |
| recommended_action | TEXT | NULL | Specific action recommended |
| action_taken | VARCHAR(255) | NULL | What actually happened (scheduled_appointment, counselor_assigned, etc.) |
| action_taken_by_user_id | INT | FOREIGN KEY | Who implemented the action |
| action_timestamp | TIMESTAMP | NULL | When action was taken |
| outcome | VARCHAR(255) | NULL | Result: completed, pending, declined, escalated |
| follow_up_status | ENUM | DEFAULT 'pending' | Status: pending, in_progress, completed, escalated |
| created_at | TIMESTAMP | NOT NULL, AUTO | Decision creation timestamp |

**Relationships**:
- N:1 with `students`
- N:1 with `users` (action_taken_by)

**Indexes**:
- `idx_student_id`: View student's DSS history
- `idx_decision_type`: Analyze decision patterns
- `idx_risk_level_determined`: Outcomes by risk level
- `idx_created_at`: Recent decisions
- `idx_follow_up_status`: Pending actions

**Decision Types**:
- `risk_assessment`: Initial risk evaluation
- `appointment_recommendation`: DSS suggests booking appointment
- `referral_suggestion`: External specialist needed
- `intervention_level`: Changes in intervention intensity
- `emergency_protocol`: Crisis response trigger

**Notes**:
- JSON input_data allows flexible algorithm evolution
- Confidence score measures DSS certainty (for manual review threshold)
- Complete audit trail for compliance and validation
- Essential for validating DSS effectiveness

---

### 11. AUDIT_LOGS Table
**Purpose**: Track all system changes for compliance and security

| Column | Type | Constraints | Purpose |
|--------|------|-----------|---------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique audit entry identifier |
| user_id | INT | FOREIGN KEY, NULL | Who made the change (NULL for system) |
| action | VARCHAR(255) | NOT NULL | Action: INSERT, UPDATE, DELETE, VIEW, EXPORT, etc. |
| entity_type | VARCHAR(100) | NULL | What was changed: users, students, appointments, etc. |
| entity_id | INT | NULL | ID of entity modified |
| old_values | JSON | NULL | Previous state (for sensitive fields) |
| new_values | JSON | NULL | New state |
| ip_address | VARCHAR(45) | NULL | Source IP address |
| created_at | TIMESTAMP | NOT NULL, AUTO | Change timestamp |

**Relationships**:
- N:1 with `users`

**Indexes**:
- `idx_user_id`: View user's actions
- `idx_action`: Filter by action type
- `idx_entity_type`: View changes to specific entity
- `idx_created_at`: Recent changes

**Notes**:
- HIPAA/FERPA compliance requirement
- Sensitive data in old_values/new_values should be masked or encrypted
- Immutable log (no deletes, only SELECTs)

---

## Relationships & Constraints

### Primary Foreign Key Relationships

```
USERS (1) ─── (1) STUDENTS
      │
      ├─── (1) COUNSELORS
      │
      └─── (N) AUDIT_LOGS

STUDENTS (1) ──── (N) SURVEY_RESPONSES ──────┐
        │                                      │
        ├── (1) SURVEY_SUMMARY                │
        │                                      ├─→ (N) SURVEY_QUESTIONS
        ├── (N) APPOINTMENTS                  │
        │        │                             │
        │        └─→ (N) COUNSELOR_NOTES ─────┘
        │
        ├── (N) COUNSELOR_ASSIGNMENTS ──→ (N) COUNSELORS
        │
        └── (N) DSS_LOGS

COUNSELORS (1) ─── (N) APPOINTMENTS
          │
          ├─ (N) COUNSELOR_NOTES
          │
          └─ (N) COUNSELOR_ASSIGNMENTS ──→ (N) STUDENTS
```

### Cascade Rules

| Foreign Key | Delete Action | Rationale |
|-------------|---------------|-----------|
| users → students | CASCADE | Delete student data when user deleted |
| users → counselors | CASCADE | Delete counselor profile when user deleted |
| students → survey_responses | CASCADE | Archive responses when student removed |
| students → appointments | CASCADE | Archive appointments when student removed |
| counselor → appointments | RESTRICT | Prevent deletion while counselor has active appointments |
| survey_questions → responses | RESTRICT | Preserve historical survey definitions |
| appointments → counselor_notes | CASCADE | Archive notes when appointment removed |
| users → audit_logs | SET NULL | Mark user as anonymous in audit trail |

---

## Entity-Relationship Diagram

### Text-Based ER Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS                                   │
├─────────────────────────────────────────────────────────────────┤
│ PK: id                                                          │
│ • name                                                          │
│ • email (UNIQUE)                                               │
│ • password_hash                                                │
│ • role (ENUM: student, counselor, admin)                      │
│ • is_active                                                    │
│ • last_login                                                   │
│ • created_at, updated_at                                       │
└──────────────────────────────────────────────────────────────┬─┘
      │
      │ (1:1)
      ├─────→ ┌──────────────────────────────────────────────────┐
      │       │           STUDENTS                              │
      │       ├──────────────────────────────────────────────────┤
      │       │ PK: id                                           │
      │       │ FK: user_id (UNIQUE)                             │
      │       │ • student_id_number (UNIQUE)                    │
      │       │ • major, year, date_of_birth                    │
      │       │ • emergency_contact_*                           │
      │       │ • is_at_risk                                    │
      │       │ • created_at, updated_at                        │
      │       └──────────────────────────────────────────────────┘
      │               │
      │               │ (1:N)
      │               ├──→ ┌──────────────────────────────────────┐
      │               │    │   SURVEY_RESPONSES                  │
      │               │    ├──────────────────────────────────────┤
      │               │    │ PK: id                              │
      │               │    │ FK: student_id, question_id         │
      │               │    │ • response_value, response_score   │
      │               │    │ • response_date                     │
      │               │    │ • survey_session_id                 │
      │               │    └──────────────────────────────────────┘
      │               │         │
      │               │         │ (N:1)
      │               │         └──→ ┌─────────────────────────────┐
      │               │              │  SURVEY_QUESTIONS           │
      │               │              ├─────────────────────────────┤
      │               │              │ PK: id                      │
      │               │              │ • category                  │
      │               │              │ • question_text             │
      │               │              │ • question_type             │
      │               │              │ • risk_weight               │
      │               │              │ • min/max_score             │
      │               │              │ • is_active, display_order  │
      │               │              └─────────────────────────────┘
      │               │
      │               ├──→ ┌──────────────────────────────────────┐
      │               │    │   SURVEY_SUMMARY                    │
      │               │    ├──────────────────────────────────────┤
      │               │    │ PK: id                              │
      │               │    │ FK: student_id (UNIQUE)             │
      │               │    │ • risk_level (ENUM)                 │
      │               │    │ • overall_score                     │
      │               │    │ • *_score fields                    │
      │               │    │ • suicidal_ideation_indicator       │
      │               │    │ • recommendations                   │
      │               │    │ • last_assessment_date              │
      │               │    └──────────────────────────────────────┘
      │               │
      │               ├──→ ┌──────────────────────────────────────┐
      │               │    │   APPOINTMENTS                      │
      │               │    ├──────────────────────────────────────┤
      │               │    │ PK: id                              │
      │               │    │ FK: student_id, counselor_id        │
      │               │    │ • appointment_date                  │
      │               │    │ • duration_minutes                  │
      │               │    │ • status (ENUM)                     │
      │               │    │ • appointment_type                  │
      │               │    │ • location, meeting_notes           │
      │               │    └──────────────────────────────────────┘
      │               │         │
      │               │         │ (1:N)
      │               │         └──→ ┌────────────────────────────┐
      │               │              │ COUNSELOR_NOTES            │
      │               │              ├────────────────────────────┤
      │               │              │ PK: id                    │
      │               │              │ FK: appointment_id        │
      │               │              │    student_id             │
      │               │              │    counselor_id           │
      │               │              │ • note_content            │
      │               │              │ • session_summary         │
      │               │              │ • follow_up_*             │
      │               │              │ • risk_assessment_update  │
      │               │              │ • referral_*              │
      │               │              └────────────────────────────┘
      │               │
      │               ├──→ ┌──────────────────────────────────────┐
      │               │    │COUNSELOR_ASSIGNMENTS                │
      │               │    ├──────────────────────────────────────┤
      │               │    │ PK: id                              │
      │               │    │ FK: student_id, counselor_id        │
      │               │    │ • assignment_date                   │
      │               │    │ • status (ENUM)                     │
      │               │    │ • reason_for_assignment             │
      │               │    │ • transferred_to_counselor_id       │
      │               │    └──────────────────────────────────────┘
      │               │
      │               └──→ ┌──────────────────────────────────────┐
      │                    │    DSS_LOGS                         │
      │                    ├──────────────────────────────────────┤
      │                    │ PK: id                              │
      │                    │ FK: student_id, action_taken_by_id  │
      │                    │ • decision_type, decision_trigger   │
      │                    │ • input_data (JSON)                 │
      │                    │ • risk_level_determined             │
      │                    │ • confidence_score                  │
      │                    │ • recommendation_type               │
      │                    │ • action_taken, action_timestamp    │
      │                    │ • outcome, follow_up_status         │
      │                    └──────────────────────────────────────┘
      │
      ├─────→ ┌──────────────────────────────────────────────────┐
      │       │          COUNSELORS                             │
      │       ├──────────────────────────────────────────────────┤
      │       │ PK: id                                           │
      │       │ FK: user_id (UNIQUE)                             │
      │       │ • license_number (UNIQUE)                       │
      │       │ • specialization                                │
      │       │ • credentials, bio                              │
      │       │ • max_clients, current_client_count             │
      │       │ • is_available                                  │
      │       └──────────────────────────────────────────────────┘
      │
      └─────→ ┌──────────────────────────────────────────────────┐
              │        AUDIT_LOGS                               │
              ├──────────────────────────────────────────────────┤
              │ PK: id                                           │
              │ FK: user_id (nullable)                           │
              │ • action                                        │
              │ • entity_type, entity_id                        │
              │ • old_values (JSON)                             │
              │ • new_values (JSON)                             │
              │ • ip_address                                    │
              └──────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
SURVEY INTAKE FLOW:
===================
Student → SURVEY_QUESTIONS → Student responds → SURVEY_RESPONSES
                                                        │
                                                        ↓
                                        CALCULATE_STUDENT_RISK_LEVEL (SP)
                                                        │
                                                        ↓
                                          SURVEY_SUMMARY (updated)
                                                        │
                                                        ↓
                                             DSS_LOGS (entry created)
                                                        │
                                    ┌───────────────────┴──────────────────┐
                                    ↓                                      ↓
                            (If Low/Medium Risk)                  (If High Risk)
                                    │                                      │
                                    ↓                                      ↓
                            Routine Counseling                    ESCALATE IMMEDIATELY
                                    │                                      │
                                    ↓                                      ↓
                        COUNSELOR_ASSIGNMENTS                  EMERGENCY APPOINTMENT
                                    │                                      │
                                    ↓                                      ↓
                            APPOINTMENTS                        URGENT NOTIFICATIONS
                                    │                                      │
                                    ↓                                      ↓
                        COUNSELOR_NOTES (session)              SPECIALIST_REFERRAL


APPOINTMENT TRACKING FLOW:
==========================
Appointment created → Scheduled date arrives → Session completed
        │                                            │
        ├─ Conflicts checked                         ├─ COUNSELOR_NOTES created
        ├─ Counselor capacity verified               ├─ SURVEY_SUMMARY potentially updated
        └─ Reminders sent                            └─ DSS_LOGS (outcome recorded)
```

---

## Indexes for Performance

### Primary Performance Indexes

#### User Authentication
```sql
INDEX idx_email (email)  -- Fast login lookups
```

#### Student Queries
```sql
INDEX idx_student_id_number (student_id_number)  -- University system integration
INDEX idx_year (year)  -- Cohort analysis
INDEX idx_is_at_risk (is_at_risk)  -- Quick high-risk identification
```

#### Survey & DSS Queries
```sql
INDEX idx_category (category)  -- Group questions
INDEX idx_is_active (is_active)  -- Filter active surveys
INDEX idx_response_date (response_date)  -- Time-based analysis
INDEX idx_survey_session_id (survey_session_id)  -- Group responses
INDEX idx_risk_level (risk_level)  -- Risk dashboard
INDEX idx_last_assessment_date (last_assessment_date)  -- Stale assessment detection
INDEX idx_action_required (action_required)  -- Priority queue
```

#### Scheduling Queries
```sql
INDEX idx_appointment_date (appointment_date)  -- Calendar queries
INDEX idx_status (status)  -- Filter by state
INDEX idx_counselor_id (counselor_id)  -- Counselor workload
```

#### Audit & Compliance
```sql
INDEX idx_created_at (created_at)  -- Recent audit entries
INDEX idx_decision_type (decision_type)  -- DSS decision analysis
INDEX idx_follow_up_status (follow_up_status)  -- Pending actions
```

#### Foreign Key Indexes
```sql
FOREIGN KEY (student_id) REFERENCES students(id)  -- Automatic index
FOREIGN KEY (question_id) REFERENCES survey_questions(id)  -- Automatic index
FOREIGN KEY (counselor_id) REFERENCES counselors(id)  -- Automatic index
```

---

## Views

### 1. v_active_students_with_counselors
**Purpose**: Consolidated student profile with assigned counselor

**Query**: Returns students with current counselor assignments and risk levels

**Use Cases**:
- Counselor dashboard to see assigned students
- Admin reports on student-counselor allocation

### 2. v_high_risk_students
**Purpose**: Immediate alert view for high-risk students

**Query**: Returns students with High risk level requiring urgent intervention

**Use Cases**:
- Crisis response team dashboard
- Daily safety check-ins
- Department head alerts

### 3. v_counselor_workload
**Purpose**: Workload analysis and capacity planning

**Query**: Aggregates counselor assignment counts and appointment metrics

**Use Cases**:
- Identify overburdened counselors
- Capacity planning
- Performance analysis

---

## Stored Procedures

### 1. calculate_student_risk_level(student_id)
**Purpose**: Compute DSS risk assessment from survey responses

**Algorithm**:
1. Average responses in each category (weighted by risk_weight)
2. Calculate overall_score = mental (0.4) + substance (0.3) + academic (0.3)
3. Check for suicidal_ideation red flags
4. Classify risk level based on thresholds
5. Update SURVEY_SUMMARY table

**Called By**: Survey completion workflow

### 2. assign_counselor_to_student(student_id, counselor_id, reason)
**Purpose**: Safely assign student to counselor with capacity checks

**Validations**:
- Counselor has capacity (current_client_count < max_clients)
- Deactivate existing assignments
- Increment counselor client count

**Error Handling**: Returns 45000 error if counselor full

---

## Normalization Analysis

### Compliance with 3NF

#### 1st Normal Form (1NF) ✓
- All attributes are atomic (no repeating groups)
- Exception: JSON fields (input_data, old_values) are semi-structured but normalized for their domain

#### 2nd Normal Form (2NF) ✓
- All non-key attributes depend on the entire primary key
- No partial dependencies on composite keys

#### 3rd Normal Form (3NF) ✓
- No transitive dependencies between non-key attributes
- All facts determinable only by primary key or functional dependencies

#### BCNF (Boyce-Codd Normal Form) ✓
- All determinants are candidate keys
- One counselor → one professional license (enforced by UNIQUE constraint)

### Identified Denormalizations (Intentional)

| Denormalization | Reason | Tradeoff |
|-----------------|--------|----------|
| current_client_count in COUNSELORS | Avoid COUNT() queries on every read | Must maintain via triggers/app logic |
| is_at_risk in STUDENTS | Quick filtering without JOIN to SURVEY_SUMMARY | Must update via stored procedure |
| student_id, counselor_id in COUNSELOR_NOTES | Faster queries without multiple JOINs | Redundant but acceptable for audit records |

---

## Implementation Guide

### Step 1: Database Creation
```bash
# Create database
mysql -u root -p
CREATE DATABASE student_mental_health_dss;
USE student_mental_health_dss;
```

### Step 2: Load Schema
```bash
mysql -u root -p student_mental_health_dss < database/schema.sql
```

### Step 3: Verify Installation
```sql
-- Verify tables created
SHOW TABLES;

-- Verify views
SHOW FULL TABLES WHERE Table_Type = 'VIEW';

-- Check table structure
DESCRIBE users;

-- Verify indexes
SHOW INDEX FROM students;

-- Check stored procedures
SHOW PROCEDURE STATUS WHERE Db = 'student_mental_health_dss';
```

### Step 4: Backup Strategy
```bash
# Daily backup
mysqldump -u root -p student_mental_health_dss > backup_$(date +%Y%m%d).sql

# Full dump with structure
mysqldump --routines --events -u root -p student_mental_health_dss > full_backup.sql
```

### Step 5: Performance Monitoring
```sql
-- Monitor table sizes
SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS `Size (MB)`
FROM information_schema.TABLES
WHERE table_schema = 'student_mental_health_dss'
ORDER BY data_length + index_length DESC;

-- Analyze slow queries
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
```

---

## Security Considerations

1. **Data Sensitivity**: All fields containing student health information must be:
   - Encrypted at rest
   - Transmitted over HTTPS only
   - Logged minimally (audit_logs table)
   - HIPAA/FERPA compliant

2. **Access Control**:
   - Database-level: Role-based permissions
   - Application-level: Authorization checks before queries
   - View-level: Students see only their own data

3. **Audit Trail**:
   - Every modification logged to audit_logs
   - Immutable audit logs (no UPDATE/DELETE)
   - Sensitive fields masked in logs

4. **Backup & Recovery**:
   - Daily encrypted backups
   - Tested restore procedures
   - Recovery time objective (RTO): < 1 hour

---

## Migration Path (Future Enhancements)

### Phase 2.1: Analytics Tables
- Add `survey_analytics` for trend analysis
- Add `dss_model_metrics` to track algorithm performance

### Phase 2.2: Notification System
- Add `notifications` table for alerts
- Add `notification_preferences` for student opt-in

### Phase 2.3: Resource Directory
- Add `resources` table for counseling services
- Add `resource_recommendations` linking DSS to resources

### Phase 2.4: Peer Support
- Add `peer_support_groups` table
- Add `peer_support_participation` for group assignments

---

## References

- **Database Design**: 3NF normalization standards
- **Scaling**: Index strategy for 10K+ students
- **Security**: HIPAA/FERPA compliance for health records
- **Audit**: SOC 2 compliance for access logging
- **Performance**: Query optimization via EXPLAIN analysis

---

*Last Updated: 2026-06-28*
*Schema Version: 1.0*
