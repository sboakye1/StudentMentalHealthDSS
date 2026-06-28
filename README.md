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
