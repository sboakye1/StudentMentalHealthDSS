from flask import render_template, jsonify, request, session, redirect, url_for, abort, flash, Response
from database import check_database_health, get_connection
import uuid
from functools import wraps
from datetime import datetime
import csv
from io import StringIO


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
                flash("You are not authorized to access that page. Please log in with the correct account.", "danger")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_dss_decision(score):
    if score <= 2:
        return {
            "risk_level": "Low",
            "priority": "Low",
            "recommendation": (
                "Continue self-care; Access online mental health resources; "
                "Retake survey in two weeks"
            ),
            "intervention_required": False,
        }
    if score <= 4:
        return {
            "risk_level": "Medium",
            "priority": "Medium",
            "recommendation": (
                "Book counseling appointment; Follow up within 7 days; "
                "Monitor student"
            ),
            "intervention_required": False,
        }
    return {
        "risk_level": "High",
        "priority": "Critical",
        "recommendation": (
            "Immediate counseling appointment; Notify counselor; "
            "Flag student for urgent intervention"
        ),
        "intervention_required": True,
    }


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


def get_logged_in_student_id():
    if "user_id" not in session or session.get("user_role") != "student":
        return None
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM students WHERE user_id = %s", (session["user_id"],))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] if result else None


def student_has_completed_survey(student_id):
    if not student_id:
        return False
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM survey_summary WHERE student_id = %s", (student_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    return count > 0


def survey_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("user_role") != "student":
            return redirect(url_for("login"))
        student_id = get_logged_in_student_id()
        if not student_id or not student_has_completed_survey(student_id):
            return redirect(url_for("student_survey"))
        return f(*args, **kwargs)
    return decorated_function


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
                    student_id = get_logged_in_student_id()
                    if student_id and student_has_completed_survey(student_id):
                        return redirect(url_for("student_dashboard"))
                    return redirect(url_for("student_survey"))
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

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            student_id_number = request.form.get("student_id_number", "").strip()
            major = request.form.get("major", "").strip()
            year = request.form.get("year", "Freshman")
            phone = request.form.get("phone", "").strip()

            errors = []
            if not name or not email or not password or not confirm_password or not student_id_number:
                errors.append("All required fields must be filled in.")
            if password != confirm_password:
                errors.append("Passwords do not match.")

            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                errors.append("Email already registered.")

            cursor.execute("SELECT id FROM students WHERE student_id_number = %s", (student_id_number,))
            if cursor.fetchone():
                errors.append("Student ID already registered.")

            if errors:
                cursor.close()
                connection.close()
                return render_template("register.html", errors=errors, form={
                    "name": name, "email": email, "student_id_number": student_id_number,
                    "major": major, "year": year, "phone": phone
                })

            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, 'student', TRUE)",
                (name, email, password)
            )
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO students (user_id, student_id_number, major, year, phone) VALUES (%s, %s, %s, %s, %s)",
                (user_id, student_id_number, major, year, phone)
            )
            connection.commit()
            cursor.close()
            connection.close()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/student/dashboard")
    @survey_required
    def student_dashboard():
        student_id = get_logged_in_student_id()
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT u.name, ss.overall_score, ss.risk_level, ss.last_assessment_date,
                   CASE ss.risk_level
                       WHEN 'High' THEN 'Critical'
                       WHEN 'Medium' THEN 'Medium'
                       WHEN 'Low' THEN 'Low'
                       ELSE 'Not Assigned'
                   END AS priority,
                   ss.recommendations, ss.action_required,
                   (SELECT COUNT(*) FROM survey_responses sr WHERE sr.student_id = %s) as total_surveys
            FROM users u
            JOIN students s ON u.id = s.user_id
            LEFT JOIN survey_summary ss ON s.id = ss.student_id
            WHERE s.id = %s
        """, (student_id, student_id))
        result = cursor.fetchone()
        cursor.execute("""
            SELECT appointment_date, status
            FROM appointments
            WHERE student_id = %s AND appointment_date >= NOW() AND status = 'scheduled'
            ORDER BY appointment_date ASC
            LIMIT 1
        """, (student_id,))
        upcoming_appointment = cursor.fetchone()
        cursor.close()
        connection.close()
        dashboard_data = {
            "name": result[0] if result else "Student",
            "score": result[1] if result and result[1] else 0,
            "risk_level": result[2] if result and result[2] else "Not Assessed",
            "last_assessment": result[3] if result and result[3] else None,
            "priority": result[4] if result and result[4] else "Not Assigned",
            "recommendation": result[5] if result and result[5] else "Complete a survey to receive a recommendation.",
            "intervention_required": bool(result[6]) if result else False,
            "total_surveys": result[7] if result else 0,
            "upcoming_appointment": upcoming_appointment
        }
        return render_template("student_dashboard.html", data=dashboard_data)

    @app.route("/student/appointments")
    @survey_required
    def student_appointments():
        student_id = get_logged_in_student_id()
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT a.appointment_date, a.status, a.appointment_type,
                   COALESCE(u.name, 'Unassigned') as counselor_name
            FROM appointments a
            LEFT JOIN counselors c ON a.counselor_id = c.id
            LEFT JOIN users u ON c.user_id = u.id
            WHERE a.student_id = %s
            ORDER BY a.appointment_date DESC
        """, (student_id,))
        appointments = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template("student_appointments.html", appointments=appointments)

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
            decision = generate_dss_decision(score)
            student_id = get_logged_in_student_id()
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO survey_responses (student_id, question_id, response_value, response_score, survey_session_id) VALUES (%s, %s, %s, %s, %s)",
                (student_id, 1, "survey_complete", score, session_id)
            )
            connection.commit()
            cursor.execute(
                """
                INSERT INTO survey_summary
                (student_id, risk_level, overall_score, recommendations, action_required, survey_completion_date)
                VALUES (%s, %s, %s, %s, %s, CURDATE())
                ON DUPLICATE KEY UPDATE
                    risk_level = %s,
                    overall_score = %s,
                    recommendations = %s,
                    action_required = %s,
                    last_assessment_date = CURRENT_TIMESTAMP
                """,
                (
                    student_id,
                    decision["risk_level"],
                    score,
                    decision["recommendation"],
                    decision["intervention_required"],
                    decision["risk_level"],
                    score,
                    decision["recommendation"],
                    decision["intervention_required"],
                )
            )
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for("student_dashboard"))
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

    @app.route("/student/appointment", methods=["GET", "POST"])
    @survey_required
    def student_appointment():
        if request.method == "POST":
            student_id = get_logged_in_student_id()
            preferred_date = request.form.get("preferred_date")
            preferred_time = request.form.get("preferred_time")
            appointment_type = request.form.get("appointment_type", "follow_up")
            reason = request.form.get("reason", "")
            appointment_datetime = f"{preferred_date} {preferred_time}"
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO appointments (student_id, counselor_id, appointment_date, appointment_type, status, meeting_notes)
                VALUES (%s, NULL, %s, %s, 'scheduled', %s)
            """, (student_id, appointment_datetime, appointment_type, reason))
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for("student_dashboard"))
        return render_template("student_appointment.html")

    @app.route("/counselor/dashboard")
    @role_required('counselor')
    def counselor_dashboard():
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        counselor_name = "Counselor"
        counselor_id = None
        cursor.execute("SELECT id, user_id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        if counselor:
            counselor_id = counselor[0]
            cursor.execute("SELECT name FROM users WHERE id = %s", (counselor[1],))
            counselor_row = cursor.fetchone()
            counselor_name = counselor_row[0] if counselor_row else "Counselor"
        assigned_students = []
        high_risk = medium_risk = low_risk = 0
        upcoming_appointments = []
        completed_sessions = 0
        appointment_requests = []
        my_appointments = []
        if counselor_id:
            cursor.execute("""
                SELECT s.id, u.name, s.student_id_number, ss.overall_score, ss.risk_level,
                       ss.last_assessment_date,
                       CASE ss.risk_level
                           WHEN 'High' THEN 'Critical'
                           WHEN 'Medium' THEN 'Medium'
                           WHEN 'Low' THEN 'Low'
                           ELSE 'Not Assigned'
                       END AS priority,
                       ss.recommendations
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN survey_summary ss ON s.id = ss.student_id
                JOIN counselor_assignments ca ON s.id = ca.student_id
                WHERE ca.counselor_id = %s AND ca.status = 'active'
                ORDER BY
                    CASE ss.risk_level
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 3
                        ELSE 4
                    END,
                    ss.last_assessment_date DESC
            """, (counselor_id,))
            assigned_students = cursor.fetchall()
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN ss.risk_level = 'High' THEN 1 END) as high_risk,
                    COUNT(CASE WHEN ss.risk_level = 'Medium' THEN 1 END) as medium_risk,
                    COUNT(CASE WHEN ss.risk_level = 'Low' THEN 1 END) as low_risk
                FROM counselor_assignments ca
                JOIN students s ON ca.student_id = s.id
                LEFT JOIN survey_summary ss ON s.id = ss.student_id
                WHERE ca.counselor_id = %s AND ca.status = 'active'
            """, (counselor_id,))
            risk_counts = cursor.fetchone()
            high_risk = risk_counts[0] or 0
            medium_risk = risk_counts[1] or 0
            low_risk = risk_counts[2] or 0
            cursor.execute("""
                SELECT u.name, a.appointment_date
                FROM appointments a
                JOIN students s ON a.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE a.counselor_id = %s AND a.appointment_date >= NOW() AND a.status = 'scheduled'
                ORDER BY a.appointment_date ASC
                LIMIT 10
            """, (counselor_id,))
            upcoming_appointments = cursor.fetchall()
            cursor.execute("""
                SELECT COUNT(*) FROM appointments
                WHERE counselor_id = %s AND status = 'completed'
            """, (counselor_id,))
            completed_sessions = cursor.fetchone()[0] or 0
            cursor.execute("""
                SELECT a.id, u.name, a.appointment_date, a.appointment_type, a.status
                FROM appointments a
                JOIN students s ON a.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE a.counselor_id = %s AND a.status = 'scheduled'
                ORDER BY a.appointment_date ASC
            """, (counselor_id,))
            my_appointments = cursor.fetchall()
        cursor.execute("""
            SELECT a.id, u.name, a.appointment_date, a.appointment_type, a.meeting_notes
            FROM appointments a
            JOIN students s ON a.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE a.counselor_id IS NULL AND a.status = 'scheduled'
            ORDER BY a.appointment_date ASC
        """)
        appointment_requests = cursor.fetchall()
        cursor.close()
        connection.close()
        counselor_data = {
            "counselor_name": counselor_name,
            "total_students": len(assigned_students),
            "high_risk_students": high_risk,
            "medium_risk_students": medium_risk,
            "low_risk_students": low_risk,
            "assigned_students": assigned_students,
            "upcoming_appointments": upcoming_appointments,
            "completed_sessions": completed_sessions,
            "appointment_requests": appointment_requests,
            "my_appointments": my_appointments
        }
        return render_template("counselor_dashboard.html", data=counselor_data)

    @app.route("/counselor/students")
    @role_required('counselor')
    def counselor_students():
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        counselor_id = counselor[0] if counselor else None
        students = []
        if counselor_id:
            cursor.execute("""
                SELECT s.id, u.name, s.student_id_number, ss.overall_score, ss.risk_level,
                       ss.last_assessment_date,
                       CASE ss.risk_level
                           WHEN 'High' THEN 'Critical'
                           WHEN 'Medium' THEN 'Medium'
                           WHEN 'Low' THEN 'Low'
                           ELSE 'Not Assigned'
                       END AS priority,
                       ss.recommendations
                FROM students s
                JOIN users u ON s.user_id = u.id
                LEFT JOIN survey_summary ss ON s.id = ss.student_id
                JOIN counselor_assignments ca ON s.id = ca.student_id
                WHERE ca.counselor_id = %s AND ca.status = 'active'
                ORDER BY
                    CASE ss.risk_level
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        WHEN 'Low' THEN 3
                        ELSE 4
                    END,
                    ss.last_assessment_date DESC
            """, (counselor_id,))
            students = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template("counselor_students.html", students=students)

    @app.route("/counselor/requests")
    @role_required('counselor')
    def counselor_requests():
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        counselor_id = counselor[0] if counselor else None
        requests = []
        if counselor_id:
            # Get unassigned requests (available for this counselor to claim)
            cursor.execute("""
                SELECT a.id, u.name, a.appointment_date, a.appointment_type, a.meeting_notes
                FROM appointments a
                JOIN students s ON a.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE a.counselor_id IS NULL AND a.status = 'scheduled'
                ORDER BY a.appointment_date ASC
            """)
            requests = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template("counselor_requests.html", requests=requests)

    @app.route("/counselor/appointments")
    @role_required('counselor')
    def counselor_appointments():
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        counselor_id = counselor[0] if counselor else None
        appointments = []
        if counselor_id:
            cursor.execute("""
                SELECT a.id, u.name, a.appointment_date, a.appointment_type, a.status
                FROM appointments a
                JOIN students s ON a.student_id = s.id
                JOIN users u ON s.user_id = u.id
                WHERE a.counselor_id = %s AND a.status = 'scheduled'
                ORDER BY a.appointment_date ASC
            """, (counselor_id,))
            appointments = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template("counselor_appointments.html", appointments=appointments)

    @app.route("/counselor/student/<int:student_id>")
    @role_required('counselor')
    def counselor_student_detail(student_id):
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        counselor_id = counselor[0] if counselor else None
        cursor.execute("""
            SELECT s.id, s.student_id_number, u.name, u.email, ss.overall_score, ss.risk_level, ss.last_assessment_date
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN survey_summary ss ON s.id = ss.student_id
            WHERE s.id = %s
        """, (student_id,))
        student = cursor.fetchone()
        cursor.execute("""
            SELECT a.id, a.appointment_date, a.status
            FROM appointments a
            WHERE a.student_id = %s AND a.counselor_id = %s
            ORDER BY a.appointment_date DESC
            LIMIT 10
        """, (student_id, counselor_id))
        appointments = cursor.fetchall()
        cursor.execute("""
            SELECT sr.response_date, sq.question_text, sr.response_value, sr.response_score
            FROM survey_responses sr
            JOIN survey_questions sq ON sr.question_id = sq.id
            WHERE sr.student_id = %s
            ORDER BY sr.response_date DESC
            LIMIT 20
        """, (student_id,))
        survey_history = cursor.fetchall()
        cursor.execute("""
            SELECT cn.id, cn.note_content, cn.session_summary, cn.mood_observed, cn.created_at
            FROM counselor_notes cn
            WHERE cn.student_id = %s AND cn.counselor_id = %s
            ORDER BY cn.created_at DESC
        """, (student_id, counselor_id))
        notes = cursor.fetchall()
        cursor.close()
        connection.close()
        student_data = {
            "student": student,
            "appointments": appointments,
            "survey_history": survey_history,
            "notes": notes
        }
        return render_template("counselor_student_detail.html", data=student_data)

    @app.route("/counselor/notes/create/<int:student_id>", methods=["GET", "POST"])
    @role_required('counselor')
    def counselor_create_note(student_id):
        if request.method == "POST":
            user_id = session.get("user_id")
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, user_id FROM counselors WHERE user_id = %s", (user_id,))
            counselor = cursor.fetchone()
            counselor_id = counselor[0] if counselor else None
            if counselor:
                appointment_id = request.form.get("appointment_id") or None
                note_content = request.form.get("note_content", "")
                session_summary = request.form.get("session_summary", "")
                mood_observed = request.form.get("mood_observed", "")
                mental_status = request.form.get("mental_status_assessment", "")
                follow_up_required = request.form.get("follow_up_required") == "on"
                follow_up_plan = request.form.get("follow_up_plan", "")
                recommended_resources = request.form.get("recommended_resources", "")
                risk_update = request.form.get("risk_assessment_update") or None
                referral_needed = request.form.get("referral_needed") == "on"
                referral_details = request.form.get("referral_details", "")
                cursor.execute("""
                    INSERT INTO counselor_notes 
                    (appointment_id, student_id, counselor_id, note_content, session_summary, mood_observed,
                     mental_status_assessment, follow_up_required, follow_up_plan, recommended_resources,
                     risk_assessment_update, referral_needed, referral_details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (appointment_id, student_id, counselor_id, note_content, session_summary, mood_observed,
                      mental_status, follow_up_required, follow_up_plan, recommended_resources,
                      risk_update, referral_needed, referral_details))
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for("counselor_student_detail", student_id=student_id))
        return redirect(url_for("counselor_student_detail", student_id=student_id))

    @app.route("/counselor/notes/edit/<int:note_id>", methods=["GET", "POST"])
    @role_required('counselor')
    def counselor_edit_note(note_id):
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        counselor_id = counselor[0] if counselor else None
        if request.method == "POST":
            note_content = request.form.get("note_content", "")
            session_summary = request.form.get("session_summary", "")
            mood_observed = request.form.get("mood_observed", "")
            mental_status = request.form.get("mental_status_assessment", "")
            follow_up_required = request.form.get("follow_up_required") == "on"
            follow_up_plan = request.form.get("follow_up_plan", "")
            recommended_resources = request.form.get("recommended_resources", "")
            risk_update = request.form.get("risk_assessment_update") or None
            referral_needed = request.form.get("referral_needed") == "on"
            referral_details = request.form.get("referral_details", "")
            cursor.execute("""
                UPDATE counselor_notes 
                SET note_content = %s, session_summary = %s, mood_observed = %s,
                    mental_status_assessment = %s, follow_up_required = %s, follow_up_plan = %s,
                    recommended_resources = %s, risk_assessment_update = %s, referral_needed = %s, referral_details = %s
                WHERE id = %s AND counselor_id = %s
            """, (note_content, session_summary, mood_observed, mental_status, follow_up_required,
                  follow_up_plan, recommended_resources, risk_update, referral_needed, referral_details,
                  note_id, counselor_id))
            connection.commit()
            cursor.execute("SELECT student_id FROM counselor_notes WHERE id = %s", (note_id,))
            result = cursor.fetchone()
            student_id = result[0] if result else None
            cursor.close()
            connection.close()
            return redirect(url_for("counselor_student_detail", student_id=student_id) if student_id else url_for("counselor_dashboard"))
        cursor.execute("""
            SELECT cn.student_id, cn.note_content, cn.session_summary, cn.mood_observed,
                   cn.mental_status_assessment, cn.follow_up_required, cn.follow_up_plan,
                   cn.recommended_resources, cn.risk_assessment_update, cn.referral_needed, cn.referral_details
            FROM counselor_notes cn
            WHERE cn.id = %s AND cn.counselor_id = %s
        """, (note_id, counselor_id))
        note = cursor.fetchone()
        cursor.close()
        connection.close()
        if not note:
            return redirect(url_for("counselor_dashboard"))
        note_data = {
            "note_id": note_id,
            "student_id": note[0],
            "note_content": note[1],
            "session_summary": note[2],
            "mood_observed": note[3],
            "mental_status_assessment": note[4],
            "follow_up_required": note[5],
            "follow_up_plan": note[6],
            "recommended_resources": note[7],
            "risk_assessment_update": note[8],
            "referral_needed": note[9],
            "referral_details": note[10]
        }
        return render_template("counselor_edit_note.html", data=note_data)

    @app.route("/counselor/appointment/<int:appointment_id>/approve", methods=["POST"])
    @role_required('counselor')
    def counselor_approve_appointment(appointment_id):
        user_id = session.get("user_id")
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM counselors WHERE user_id = %s", (user_id,))
        counselor = cursor.fetchone()
        counselor_id = counselor[0] if counselor else None
        cursor.execute("""
            UPDATE appointments
            SET counselor_id = %s
            WHERE id = %s AND counselor_id IS NULL AND status = 'scheduled'
        """, (counselor_id, appointment_id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for("counselor_dashboard"))

    @app.route("/counselor/appointment/<int:appointment_id>/reject", methods=["POST"])
    @role_required('counselor')
    def counselor_reject_appointment(appointment_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE appointments
            SET status = 'cancelled'
            WHERE id = %s AND counselor_id IS NULL AND status = 'scheduled'
        """, (appointment_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for("counselor_dashboard"))

    @app.route("/counselor/appointment/<int:appointment_id>/complete", methods=["POST"])
    @role_required('counselor')
    def counselor_complete_appointment(appointment_id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE appointments
            SET status = 'completed'
            WHERE id = %s AND status = 'scheduled'
        """, (appointment_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for("counselor_dashboard"))

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
        cursor.execute("SELECT COUNT(*) FROM survey_summary WHERE risk_level = 'High'")
        critical_cases = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM survey_summary WHERE action_required = TRUE")
        intervention_required = cursor.fetchone()[0]
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
            "critical_cases": critical_cases,
            "intervention_required": intervention_required,
            "total_surveys": total_surveys,
            "recent_submissions": recent_submissions
        }
        return render_template("admin_dashboard.html", data=admin_data)

    @app.route("/api/admin/risk-distribution")
    @role_required('admin')
    def api_risk_distribution():
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT risk_level, COUNT(*) 
            FROM survey_summary 
            GROUP BY risk_level
        """)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        counts = {"Low": 0, "Medium": 0, "High": 0}
        for risk_level, count in rows:
            counts[risk_level] = count
        return jsonify(counts)

    @app.route("/api/admin/monthly-surveys")
    @role_required('admin')
    def api_monthly_surveys():
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT DATE_FORMAT(survey_completion_date, '%%Y-%%m') as month_key, COUNT(*) as survey_count
            FROM survey_summary
            WHERE survey_completion_date >= DATE_SUB(DATE_FORMAT(NOW(), '%%Y-%%m-01'), INTERVAL 5 MONTH)
            GROUP BY month_key
            ORDER BY month_key ASC
        """)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        counts = {row[0]: row[1] for row in rows}

        now = datetime.now()
        labels = []
        values = []
        for i in range(5, -1, -1):
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            month_key = f"{year:04d}-{month:02d}"
            dt = datetime(year, month, 1)
            labels.append(dt.strftime('%b %Y'))
            values.append(counts.get(month_key, 0))

        return jsonify({
            "monthly_completed_surveys": {
                "labels": labels,
                "values": values
            }
        })

    @app.route("/api/admin/appointment-stats")
    @role_required('admin')
    def api_appointment_stats():
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM appointments 
            GROUP BY status
        """)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        stats = {
            "scheduled": 0,
            "completed": 0,
            "cancelled": 0
        }
        for status, count in rows:
            if status in stats:
                stats[status] = count
        return jsonify(stats)

    @app.route("/api/admin/counselor-workload")
    @role_required('admin')
    def api_counselor_workload():
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
                u.name AS counselor_name,
                COUNT(DISTINCT CASE WHEN ca.status = 'active' THEN ca.student_id END) AS assigned_students,
                COUNT(DISTINCT CASE WHEN a.status = 'scheduled' THEN a.id END) AS scheduled_appointments
            FROM counselors c
            JOIN users u ON c.user_id = u.id
            LEFT JOIN counselor_assignments ca ON c.id = ca.counselor_id
            LEFT JOIN appointments a ON c.id = a.counselor_id AND a.appointment_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY c.id, u.name
            ORDER BY assigned_students DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        workload = []
        for row in rows:
            workload.append({
                "counselor_name": row[0],
                "assigned_students": row[1] or 0,
                "scheduled_appointments": row[2] or 0
            })
        return jsonify(workload)

    @app.route("/api/admin/critical-cases")
    @role_required('admin')
    def api_critical_cases():
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT u.name, u.email, s.student_id_number, ss.overall_score, ss.last_assessment_date, ss.suicidal_ideation_indicator
            FROM survey_summary ss
            JOIN students s ON ss.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE ss.priority = 'Critical'
            ORDER BY ss.last_assessment_date DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        cases = []
        for row in rows:
            cases.append({
                "name": row[0],
                "email": row[1],
                "student_id_number": row[2],
                "overall_score": float(row[3]) if row[3] else None,
                "last_assessment_date": row[4].isoformat() if row[4] else None,
                "suicidal_ideation_indicator": bool(row[5])
            })
        return jsonify(cases)

    @app.route("/admin/reports")
    @role_required('admin')
    def admin_reports():
        search = request.args.get('search', '').strip()
        risk_level = request.args.get('risk_level', 'all').lower()
        intervention = request.args.get('intervention', 'all').lower()
        appointment_status = request.args.get('appointment_status', 'all').lower()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT 
                s.id,
                u.name,
                s.student_id_number,
                ss.risk_level,
                ss.overall_score,
                CASE ss.risk_level
                    WHEN 'High' THEN 'Critical'
                    WHEN 'Medium' THEN 'Medium'
                    WHEN 'Low' THEN 'Low'
                    ELSE 'Not Assigned'
                END AS priority,
                ss.recommendations,
                ss.action_required,
                ss.last_assessment_date,
                ss.survey_completion_date,
                a.status AS appointment_status,
                a.appointment_date
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN survey_summary ss ON s.id = ss.student_id
            LEFT JOIN (
                SELECT a1.student_id, a1.status, a1.appointment_date
                FROM appointments a1
                INNER JOIN (
                    SELECT student_id, MAX(appointment_date) AS max_date
                    FROM appointments
                    GROUP BY student_id
                ) a2 ON a1.student_id = a2.student_id AND a1.appointment_date = a2.max_date
            ) a ON s.id = a.student_id
            WHERE u.is_active = TRUE
        """
        params = []

        if search:
            query += " AND u.name LIKE %s"
            params.append(f"%{search}%")

        if risk_level != 'all':
            query += " AND ss.risk_level = %s"
            params.append(risk_level.capitalize())

        if intervention != 'all':
            query += " AND ss.action_required = %s"
            params.append(intervention == 'yes')

        if appointment_status != 'all':
            query += " AND a.status = %s"
            params.append(appointment_status)

        query += """
            GROUP BY s.id, u.name, s.student_id_number, ss.risk_level, ss.overall_score,
                     ss.recommendations, ss.action_required, ss.last_assessment_date,
                     ss.survey_completion_date, a.status, a.appointment_date
            ORDER BY 
                CASE ss.risk_level
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END,
                ss.last_assessment_date DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        reports = []
        for row in rows:
            reports.append({
                'id': row[0],
                'name': row[1],
                'student_id_number': row[2],
                'risk_level': row[3] if row[3] else 'Not Assessed',
                'overall_score': row[4],
                'priority': row[5] if row[5] else 'Not Assigned',
                'recommendations': row[6] if row[6] else 'N/A',
                'action_required': bool(row[7]) if row[7] is not None else False,
                'last_assessment_date': row[8],
                'survey_completion_date': row[9],
                'appointment_status': row[10] if row[10] else 'None',
                'appointment_date': row[11]
            })

        return render_template("admin_reports.html", reports=reports, filters={
            'search': search,
            'risk_level': risk_level,
            'intervention': intervention,
            'appointment_status': appointment_status
        })

    @app.route("/admin/reports/export")
    @role_required('admin')
    def admin_reports_export():
        search = request.args.get('search', '').strip()
        risk_level = request.args.get('risk_level', 'all').lower()
        intervention = request.args.get('intervention', 'all').lower()
        appointment_status = request.args.get('appointment_status', 'all').lower()

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            SELECT 
                u.name,
                s.student_id_number,
                ss.risk_level,
                ss.overall_score,
                CASE ss.risk_level
                    WHEN 'High' THEN 'Critical'
                    WHEN 'Medium' THEN 'Medium'
                    WHEN 'Low' THEN 'Low'
                    ELSE 'Not Assigned'
                END AS priority,
                ss.recommendations,
                ss.action_required,
                ss.last_assessment_date,
                ss.survey_completion_date,
                a.status AS appointment_status
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN survey_summary ss ON s.id = ss.student_id
            LEFT JOIN (
                SELECT a1.student_id, a1.status
                FROM appointments a1
                INNER JOIN (
                    SELECT student_id, MAX(appointment_date) AS max_date
                    FROM appointments
                    GROUP BY student_id
                ) a2 ON a1.student_id = a2.student_id AND a1.appointment_date = a2.max_date
            ) a ON s.id = a.student_id
            WHERE u.is_active = TRUE
        """
        params = []

        if search:
            query += " AND u.name LIKE %s"
            params.append(f"%{search}%")

        if risk_level != 'all':
            query += " AND ss.risk_level = %s"
            params.append(risk_level.capitalize())

        if intervention != 'all':
            query += " AND ss.action_required = %s"
            params.append(intervention == 'yes')

        if appointment_status != 'all':
            query += " AND a.status = %s"
            params.append(appointment_status)

        query += """
            GROUP BY s.id, u.name, s.student_id_number, ss.risk_level, ss.overall_score,
                     ss.recommendations, ss.action_required, ss.last_assessment_date,
                     ss.survey_completion_date, a.status
            ORDER BY 
                CASE ss.risk_level
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END,
                ss.last_assessment_date DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Student Name', 'Student ID', 'Risk Level', 'Priority',
            'Recommendation', 'Intervention Required', 'Last Survey Date',
            'Last Assessment Date', 'Appointment Status'
        ])

        for row in rows:
            writer.writerow([
                row[0],
                row[1],
                row[2] if row[2] else 'Not Assessed',
                row[4] if row[4] else 'Not Assigned',
                row[5] if row[5] else 'N/A',
                'Yes' if row[6] else 'No',
                row[8].strftime('%Y-%m-%d') if row[8] else 'N/A',
                row[7].strftime('%Y-%m-%d %H:%M') if row[7] else 'N/A',
                row[9] if row[9] else 'None'
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=admin_reports.csv'}
        )

    @app.route("/admin/student/<int:student_id>/report")
    @role_required('admin')
    def admin_student_report(student_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT u.name, s.student_id_number, s.major, s.year, s.phone,
                   ss.risk_level, ss.overall_score,
                   CASE ss.risk_level
                       WHEN 'High' THEN 'Critical'
                       WHEN 'Medium' THEN 'Medium'
                       WHEN 'Low' THEN 'Low'
                       ELSE 'Not Assigned'
                   END AS priority,
                   ss.recommendations, ss.action_required,
                   ss.last_assessment_date, ss.survey_completion_date
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN survey_summary ss ON s.id = ss.student_id
            WHERE s.id = %s
        """, (student_id,))
        student_info = cursor.fetchone()

        if not student_info:
            cursor.close()
            connection.close()
            flash("Student not found.", "danger")
            return redirect(url_for("admin_reports"))

        cursor.execute("""
            SELECT DATE(sr.response_date) as survey_date,
                   COUNT(*) as question_count,
                   SUM(sr.response_score) as total_score
            FROM survey_responses sr
            WHERE sr.student_id = %s
            GROUP BY DATE(sr.response_date)
            ORDER BY survey_date DESC
        """, (student_id,))
        survey_history = cursor.fetchall()

        cursor.execute("""
            SELECT a.appointment_date, a.appointment_type, a.status,
                   c.id AS counselor_id, u.name AS counselor_name
            FROM appointments a
            LEFT JOIN counselors c ON a.counselor_id = c.id
            LEFT JOIN users u ON c.user_id = u.id
            WHERE a.student_id = %s
            ORDER BY a.appointment_date DESC
        """, (student_id,))
        appointments = cursor.fetchall()

        cursor.execute("""
            SELECT cn.note_content, cn.created_at, u.name AS counselor_name
            FROM counselor_notes cn
            LEFT JOIN counselors c ON cn.counselor_id = c.id
            LEFT JOIN users u ON c.user_id = u.id
            WHERE cn.student_id = %s
            ORDER BY cn.created_at DESC
        """, (student_id,))
        notes = cursor.fetchall()

        cursor.close()
        connection.close()

        student_data = {
            'student': student_info,
            'survey_history': survey_history,
            'appointments': appointments,
            'notes': notes
        }

        return render_template("admin_student_report.html", data=student_data)
