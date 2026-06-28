from flask import render_template, jsonify, request
from database import check_database_health, get_connection
import uuid


def _get_or_create_dev_student():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM students WHERE id = 1")
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('Dev Student', 'dev@example.com', 'placeholder', 'student')")
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (user_id, student_id_number) VALUES (%s, %s)", (user_id, 'DEV001'))
        connection.commit()
        student_id = cursor.lastrowid
    else:
        student_id = result[0]
    cursor.close()
    connection.close()
    return student_id


def register_routes(app):

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/student/dashboard")
    def student_dashboard():
        return render_template("student_dashboard.html")

    @app.route("/student/survey", methods=["GET", "POST"])
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

    @app.route("/api/health")
    def health_check():
        result = check_database_health()
        return jsonify({
            "application": "running",
            "database": result
        })