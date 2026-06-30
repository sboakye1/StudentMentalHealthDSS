from flask import render_template, jsonify, request, session, redirect, url_for, abort
from database import check_database_health, get_connection
import uuid
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("user_role") != role:
                expected_dashboard = f"{role}_dashboard"
                return redirect(url_for(expected_dashboard))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def _get_or_create_dev_student():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM students LIMIT 1")
    result = cursor.fetchone()
    if result:
        student_id = result[0]
    else:
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('Dev Student', 'dev@example.com', 'placeholder', 'student')")
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (user_id, student_id_number) VALUES (%s, %s)", (user_id, 'DEV001'))
        connection.commit()
        student_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return student_id


def register_routes(app):

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, name, password_hash, role FROM users WHERE email = %s AND is_active = TRUE",
                (email,)
            )
            user = cursor.fetchone()
            cursor.close()
            connection.close()
            if user and user[2] == password:
                session["user_id"] = user[0]
                session["user_name"] = user[1]
                session["user_role"] = user[3]
                if user[3] == "student":
                    return redirect(url_for("student_dashboard"))
                elif user[3] == "counselor":
                    return redirect(url_for("counselor_dashboard"))
                elif user[3] == "admin":
                    return redirect(url_for("admin_dashboard"))
            else:
                error = "Invalid email or password."
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/student/dashboard")
    @role_required('student')
    def student_dashboard():
        student_id = _get_or_create_dev_student()
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT u.name, ss.overall_score, ss.risk_level, ss.last_assessment_date,
                   (SELECT COUNT(*) FROM survey_responses sr WHERE sr.student_id = %s) as total_surveys
            FROM users u
            JOIN students s ON u.id = s.user_id
            LEFT JOIN survey_summary ss ON s.id = ss.student_id
            WHERE s.id = %s
        """, (student_id, student_id))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        dashboard_data = {
            "name": result[0] if result else "Student",
            "score": result[1] if result and result[1] else 0,
            "risk_level": result[2] if result and result[2] else "Not Assessed",
            "last_assessment": result[3] if result and result[3] else None,
            "total_surveys": result[4] if result else 0
        }
        return render_template("student_dashboard.html", data=dashboard_data)

    @app.route("/student/survey", methods=["GET", "POST"])
    @role_required('student')
    def student_survey():
        session_id = str(uuid.uuid4())
        if request.method == "POST":
            score = 0
            question_ids = []
            for key, value in request.form.items():
                if key.startswith("question_"):
                    question_id = key.replace("question_", "")
                    question_ids.append(question_id)
                    if value == "yes":
                        score += 1
            if score <= 2:
                risk_level = "Low"
            elif score <= 4:
                risk_level = "Medium"
            else:
                risk_level = "High"
            student_id = _get_or_create_dev_student()
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO survey_responses (student_id, question_id, response_value, response_score, survey_session_id) VALUES (%s, %s, %s, %s, %s)",
                (student_id, 1, "survey_complete", score, session_id)
            )
            connection.commit()
            cursor.execute(
                "INSERT INTO survey_summary (student_id, risk_level, overall_score, survey_completion_date) VALUES (%s, %s, %s, CURDATE()) ON DUPLICATE KEY UPDATE risk_level = %s, overall_score = %s, last_assessment_date = CURRENT_TIMESTAMP",
                (student_id, risk_level, score, risk_level, score)
            )
            connection.commit()
            cursor.close()
            connection.close()
            return render_template("student_survey.html", result={"score": score, "risk_level": risk_level})
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, question_text FROM survey_questions WHERE is_active = TRUE ORDER BY display_order")
        questions = cursor.fetchall()
        cursor.close()
        connection.close()
        if not questions:
            questions = [
                (1, "Do you often feel stressed about your academic performance?"),
                (2, "Do you have difficulty concentrating during classes?"),
                (3, "Do you feel isolated from your peers?"),
                (4, "Do you experience trouble sleeping due to stress?"),
                (5, "Do you feel overwhelmed with your workload?")
            ]
        return render_template("student_survey.html", questions=questions, result=None)

    @app.route("/counselor/dashboard")
    @role_required('counselor')
    def counselor_dashboard():
        return render_template("counselor_dashboard.html")

    @app.route("/api/health")
    def health_check():
        result = check_database_health()
        return jsonify({
            "application": "running",
            "database": result
        })

    @app.route("/admin/dashboard")
    @role_required('admin')
    def admin_dashboard():
        from flask import current_app
        import routes
        import os
        print(f"DEBUG view_functions: {list(current_app.view_functions.keys())}")
        print(f"DEBUG url_map: {list(current_app.url_map.iter_rules())}")
        print(f"DEBUG routes module path: {routes.__file__}")
        print(f"DEBUG template_folder: {current_app.template_folder}")
        print(f"DEBUG template exists: {os.path.exists(os.path.join(current_app.template_folder, 'counselor_dashboard.html'))}")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM survey_summary WHERE risk_level = 'High'")
        high_risk = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM survey_summary WHERE risk_level = 'Medium'")
        medium_risk = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM survey_summary WHERE risk_level = 'Low'")
        low_risk = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM survey_responses")
        total_surveys = cursor.fetchone()[0]
        cursor.execute("""
            SELECT u.name, ss.survey_completion_date, ss.risk_level, ss.overall_score
            FROM survey_summary ss
            JOIN students s ON ss.student_id = s.id
            JOIN users u ON s.user_id = u.id
            ORDER BY ss.last_assessment_date DESC
            LIMIT 10
        """)
        recent_submissions = cursor.fetchall()
        cursor.close()
        connection.close()
        admin_data = {
            "total_students": total_students,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "total_surveys": total_surveys,
            "recent_submissions": recent_submissions
        }
        return render_template("admin_dashboard.html", data=admin_data)