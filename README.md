# Student Mental Health Resource Decision Support System

## Overview
This project is the initial foundation for a Flask-based decision support system aimed at helping students access mental health resources more effectively.

## Technologies Used
- Python
- Flask
- Jinja2
- HTML/CSS
- MySQL (via XAMPP)

## Prerequisites
- Python 3.8+
- XAMPP (for MySQL)

## Local Setup

### 1. Environment Configuration
1. Copy `.env.example` to `.env`:
   ```
   copy .env.example .env
   ```
2. Edit `.env` with your database credentials:
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=student_mental_health_dss
   DB_PORT=3306
   ```

### 2. Database Setup

#### Start XAMPP MySQL
1. Open XAMPP Control Panel
2. Click "Start" button next to **MySQL**
3. Verify that MySQL is running (green indicator)
4. Alternative (Command Line):
   ```
   xampp_path\mysql\bin\mysqld.exe
   ```

#### Create Database
1. Open MySQL in XAMPP or use MySQL command line:
   ```
   mysql -u root -p
   ```
   (Press Enter if no password)

2. Create the database:
   ```sql
   CREATE DATABASE student_mental_health_dss;
   USE student_mental_health_dss;
   ```

3. Verify database creation:
   ```sql
   SHOW DATABASES;
   ```

#### Load Database Schema
After creating the database, load the complete schema with all tables, indexes, views, and stored procedures:

```bash
mysql -u root -p student_mental_health_dss < database/schema.sql
```

**Verify Schema Installation:**
```bash
mysql -u root -p student_mental_health_dss
```

Then run in MySQL:
```sql
-- Check tables created
SHOW TABLES;

-- Check views
SHOW FULL TABLES WHERE Table_Type = 'VIEW';

-- Verify sample survey questions were inserted
SELECT COUNT(*) FROM survey_questions;
```

Expected output: 15 tables + 3 views created, and 15 survey questions inserted

### 3. Python Application Setup
1. Create and activate a virtual environment:
   - `python -m venv venv`
   - `venv\Scripts\activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the application:
   - `python app.py`
4. Open your browser at:
   - `http://127.0.0.1:5000/`

## Testing Database Connection

### 1. Health Check Endpoint
Once the application is running, test the database connection using:

**Web Browser:**
- Navigate to: `http://127.0.0.1:5000/api/health`

**cURL Command:**
```bash
curl http://127.0.0.1:5000/api/health
```

**Expected Successful Response (HTTP 200):**
```json
{
  "application": "running",
  "database": {
    "status": "connected",
    "message": "Database connection is healthy",
    "database": "student_mental_health_dss",
    "version": "8.0.27"
  }
}
```

**Expected Error Response if MySQL is not running (HTTP 503):**
```json
{
  "application": "running",
  "database": {
    "status": "error",
    "message": "Cannot connect to MySQL on localhost:3306. Is MySQL running? Make sure XAMPP MySQL service is started."
  }
}
```

### 2. Troubleshooting

**Issue: "Cannot connect to MySQL on localhost:3306"**
- Solution: Start XAMPP MySQL service
- Check if MySQL is running in XAMPP Control Panel

**Issue: "Access denied for user 'root@localhost'"**
- Solution: Check your DB_PASSWORD in .env file
- Verify MySQL root password matches

**Issue: "Database 'student_mental_health_dss' does not exist"**
- Solution: Create the database using the steps in "Create Database" section above

## Project Structure
- app.py: Application entry point
- config/: Configuration and app factory with environment variables
- database/: Database connection module and utilities
- routes/: Route registration and API endpoints
- templates/: HTML templates
- static/: CSS, JavaScript, and images
- controllers/, models/, services/, utils/: Reserved for future development

## Database Module

The `database/` module provides:

### `get_connection()`
Establishes a connection to MySQL database with proper error handling.

```python
from database import get_connection, close_connection

connection = get_connection()
# Use connection...
close_connection(connection)
```

### `check_database_health()`
Performs health check on database connection. Returns status and version information.

```python
from database import check_database_health

result = check_database_health()
if result['status'] == 'connected':
    print(f"Connected to {result['database']} - MySQL {result['version']}")
```

### `get_database_config()`
Returns database configuration from environment variables.

```python
from database import get_database_config

config = get_database_config()
```

## Deployment Readiness
The project is structured for deployment with environment-based configuration and an application factory pattern. Secrets and environment-specific values are supplied through environment variables in the `.env` file.

## Database Schema Documentation

### Overview
The application uses a comprehensive MySQL schema designed for the DSS system. The schema includes:

- **11 core tables**: users, students, counselors, survey_questions, survey_responses, survey_summary, appointments, counselor_assignments, counselor_notes, dss_logs, audit_logs
- **3 views**: v_active_students_with_counselors, v_high_risk_students, v_counselor_workload
- **2 stored procedures**: calculate_student_risk_level, assign_counselor_to_student

### Key Features
✓ 3NF Normalization for data integrity  
✓ Comprehensive indexing for performance  
✓ Referential integrity with cascading rules  
✓ HIPAA/FERPA compliance design  
✓ Complete audit trail tracking  
✓ DSS decision logging and tracking  

### Documentation Files
- **[SCHEMA_DOCUMENTATION.md](database/SCHEMA_DOCUMENTATION.md)**: Complete schema design with entity relationships, normalization analysis, and implementation guide
- **[QUICK_REFERENCE.md](database/QUICK_REFERENCE.md)**: Quick lookup for common queries and operations
- **[schema.sql](database/schema.sql)**: Complete SQL schema with all DDL statements

### Understanding the Schema

#### Main Entities
- **Users**: Authentication and role management (student, counselor, admin)
- **Students**: Student profiles with risk tracking
- **Counselors**: Counselor credentials and workload management
- **Survey System**: Questions, responses, and risk summaries
- **Appointments**: Scheduling and session tracking
- **DSS Logs**: Decision tracking and audit trail

#### Data Flow
Survey Intake → Risk Calculation → DSS Decision → Appointment Assignment → Session Documentation

### Important Tables for Development

**survey_questions**: Master list of assessment questions (15 sample questions included)

**survey_responses**: Individual student survey answers (collected during assessment)

**survey_summary**: Cached DSS calculation results with risk levels

**dss_logs**: Complete decision history for auditing and validation

### First-Time Schema Verification
After loading schema.sql, verify with:
```bash
# Check table count (should show 11 tables)
mysql -u root -p student_mental_health_dss -e "SELECT COUNT(*) AS TableCount FROM information_schema.TABLES WHERE TABLE_SCHEMA='student_mental_health_dss';"

# Check view count (should show 3 views)
mysql -u root -p student_mental_health_dss -e "SELECT COUNT(*) AS ViewCount FROM information_schema.TABLES WHERE TABLE_SCHEMA='student_mental_health_dss' AND TABLE_TYPE='VIEW';"

# Check stored procedures (should show 2 procedures)
mysql -u root -p student_mental_health_dss -e "SHOW PROCEDURE STATUS WHERE Db='student_mental_health_dss';"
```
