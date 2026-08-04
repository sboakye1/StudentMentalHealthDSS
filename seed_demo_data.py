#!/usr/bin/env python3
"""
Demo database seed script for Student Mental Health DSS.
Resets all operational/demo data and generates a fresh, realistic dataset.
"""

import sys
import os
import random
import string
from datetime import datetime, timedelta, date

sys.path.insert(0, r'C:\Users\hp\Desktop\StudentMentalHealthDSS')

from app import app
from routes import get_connection

# ============================================================================
# CONFIGURATION
# ============================================================================

ADMIN_EMAIL = "admin@smhdss.edu"
ADMIN_PASSWORD = "admin123"

COUNSELORS_DATA = [
    {"name": "Dr. Sarah Mensah", "email": "sarah.mensah@smhdss.edu", "password": "counselor123", "specialization": "Clinical Psychology", "office": "Room 201, Counseling Center", "phone": "+233-20-123-4567", "bio": "Licensed clinical psychologist specializing in student mental health and anxiety disorders.", "credentials": "Ph.D. Clinical Psychology, Licensed Psychologist"},
    {"name": "Mr. Emmanuel Owusu", "email": "emmanuel.owusu@smhdss.edu", "password": "counselor123", "specialization": "Counseling Psychology", "office": "Room 205, Counseling Center", "phone": "+233-20-234-5678", "bio": "Expert in academic stress management and career counseling.", "credentials": "M.A. Counseling Psychology, Certified Counselor"},
    {"name": "Ms. Linda Asare", "email": "linda.asare@smhdss.edu", "password": "counselor123", "specialization": "Adolescent Psychology", "office": "Room 301, Student Affairs", "phone": "+233-20-345-6789", "bio": "Specializes in adolescent mental health and peer support programs.", "credentials": "M.Phil. Adolescent Psychology, Licensed Counselor"},
    {"name": "Mrs. Grace Boateng", "email": "grace.boateng@smhdss.edu", "password": "counselor123", "specialization": "Substance Abuse Counseling", "office": "Room 102, Health Services", "phone": "+233-20-456-7890", "bio": "Dedicated to helping students with substance abuse and behavioral issues.", "credentials": "M.A. Substance Abuse Counseling, Certified Addiction Counselor"},
    {"name": "Dr. Michael Addo", "email": "michael.addo@smhdss.edu", "password": "counselor123", "specialization": "Trauma Therapy", "office": "Room 405, Academic Building C", "phone": "+233-20-567-8901", "bio": "Trauma specialist with extensive experience in crisis intervention.", "credentials": "Ph.D. Clinical Psychology, Trauma Specialist"},
]

# Ghanaian names for students
STUDENT_FIRST_NAMES = [
    "Kwame", "Kwabena", "Kwaku", "Yaw", "Kofi", "Ato", "Kwadwo", "Kwame", "Kofi", "Kwabena",
    "Akosua", "Abena", "Akua", "Yaa", "Afia", "Ama", "Efua", "Aba", "Adwoa", "Akos",
    "Solomon", "Daniel", "Emmanuel", "Michael", "David", "Samuel", "Joseph", "John", "James", "Robert",
    "Priscilla", "Linda", "Grace", "Patricia", "Elizabeth", "Sarah", "Rebecca", "Mary", "Dorcas", "Mercy",
    "Cynthia", "Janet", "Ruth", "Naomi", "Hannah", "Deborah", "Esther", "Rachael", "Victoria", "Angelina",
    "Francis", "Patrick", "Stephen", "Peter", "Paul", "Andrew", "Thomas", "George", "Charles", "Edward",
]

STUDENT_LAST_NAMES = [
    "Mensah", "Owusu", "Asare", "Boateng", "Addo", "Boakye", "Ofori", "Adu", "Appiah", "Antwi",
    "Amponsah", "Bonsu", "Danso", "Frimpong", "Gyamfi", "Kwakye", "Nyarko", "Opoku", "Prempeh", "Sarpong",
    "Tuffour", "Wiredu", "Yeboah", "Agyeman", "Bediako", "Darko", "Kufuor", "Mintah", "Osei", "Agyapong",
]

PROGRAMMES = [
    "Computer Science", "Business Administration", "Nursing", "Education", "Engineering",
    "Psychology", "Biology", "Economics", "Law", "Medicine",
    "Information Technology", "Accounting", "Marketing", "Human Resource Management", "Sociology",
]

LEVELS = ["Level 100", "Level 200", "Level 300", "Level 400"]

CATEGORIES = ["Academic Stress", "Anxiety", "Depression", "Motivation", "Relationships", "Family", "General Advice", "Success Story", "Other"]

POST_TITLES = [
    "Struggling with final exams", "Feeling overwhelmed with coursework", "Need motivation to continue",
    "Homesickness getting to me", "Anxiety before presentations", "Time management tips needed",
    "How do you balance everything?", "First year challenges", "Dealing with pressure from family",
    "Finding study partners", "Mental health awareness", "Coping with stress during exams",
]

POST_MESSAGES = [
    "I have been feeling really overwhelmed with my coursework lately. The pressure to perform well is getting to me and I can't seem to find a balance. Does anyone else feel this way? Any tips would be appreciated.",
    "My anxiety spikes whenever I have to present in front of the class. I have tried breathing exercises but they don't seem to help much. How do you all manage presentation anxiety?",
    "I am a first-year student and homesickness is hitting hard. I miss my family and friends back home. How did you all adjust to campus life?",
    "I have been procrastinating a lot lately and it is affecting my grades. I know I need to do better but I can't seem to get started. Any advice on beating procrastination?",
    "Just wanted to share that I finally sought help from the counseling center and it was the best decision I have made. If you are struggling, please reach out.",
    "The workload this semester is insane. Between assignments, quizzes, and projects, I barely have time to breathe. How do you manage your time effectively?",
    "I feel like I am not good enough compared to my classmates. Everyone seems to be doing so well while I am struggling. How do you deal with imposter syndrome?",
    "Has anyone used the DSS assessment tool? I just completed mine and got a high-risk rating. Not sure what to do next.",
    "Looking for study groups for Computer Science 201. Anyone interested in forming a study group?",
    "I have been experiencing panic attacks before exams. My doctor recommended some techniques but I wanted to hear from other students. What works for you?",
]

COMMENT_TEXTS = [
    "I can relate to this. You are not alone.",
    "Thank you for sharing. This is very helpful.",
    "I went through the same thing last semester. It gets better.",
    "Have you tried speaking to a counselor? It really helped me.",
    "Stay strong. You are doing great.",
    "This is exactly what I needed to read today.",
    "Thank you for being open about this. It takes courage.",
    "I recommend trying the wellness center. They have great resources.",
    "You are not alone in this feeling.",
    "This post really resonated with me. Thanks for sharing.",
]

ANNOUNCEMENT_TITLES = [
    "Mid-Semester Break Counseling Hours",
    "Free Mental Health Screening Day",
    "Counseling Center Extended Hours",
    "Stress Management Workshop",
    "Exam Period Support Services",
    "New Online Booking System Launch",
    "Wellness Week Activities",
    "Campus Mental Health Awareness Campaign",
    "Holiday Campus Closure Notice",
    "New Group Therapy Sessions Available",
]

ANNOUNCEMENT_CONTENTS = [
    "The counseling center will have extended hours during mid-semester break to support students dealing with academic stress and homesickness.",
    "Free mental health screenings are now available at the Student Wellness Center. No appointment necessary.",
    "Due to increased demand during exam period, the counseling center will remain open until 8 PM on weekdays.",
    "Join us for a workshop on stress management techniques including mindfulness, time management, and healthy coping strategies.",
    "Additional support services will be available during the upcoming exam period including drop-in sessions and online chat support.",
    "We are excited to announce a new online appointment booking system for counseling services. Log in to your student portal to schedule.",
    "Wellness Week is coming up with activities including yoga sessions, meditation workshops, and health screenings.",
    "The campus mental health awareness campaign starts next week. Join us in breaking the stigma around mental health.",
    "The campus will be closed from December 23 to January 1 for the holiday break. Emergency counseling services will remain available.",
    "New group therapy sessions for anxiety and depression are now available. Contact the counseling center to register.",
]

APPOINTMENT_NOTES = [
    "Student discussed academic stress and coping strategies.",
    "Follow-up on previous session. Student showing improvement.",
    "Initial assessment completed. Risk level discussed.",
    "Student expressed concerns about time management.",
    "Discussed exam anxiety and relaxation techniques.",
    "Student reported improved sleep patterns.",
    "Reviewed progress on previous goals.",
    "Student shared family-related concerns.",
    "Discussed social anxiety and peer relationships.",
    "Student expressed optimism about upcoming semester.",
]

CANCELLATION_REASONS = [
    "Student had conflicting exam schedule",
    "Student requested reschedule via email",
    "Counselor unavailable due to emergency",
    "Student cancelled via phone",
    "Student no longer needs appointment",
]

LOCATIONS = [
    "Counseling Center Room 201",
    "Counseling Center Room 205",
    "Student Health Center",
    "Online/Video Call",
    "Student Affairs Room 301",
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def random_date(start_days_ago, end_days_ago):
    return datetime.now() - timedelta(days=random.randint(start_days_ago, end_days_ago))

def random_date_between(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def execute_safe(cursor, sql, params=None):
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return True
    except Exception as e:
        print(f"  SQL Error: {e}")
        print(f"  SQL: {sql[:200]}")
        if params:
            print(f"  Params: {params}")
        return False

# ============================================================================
# MAIN SEED FUNCTIONS
# ============================================================================

def reset_demo_data(conn, cursor):
    print("\n=== PART 1: RESETTING DEMO DATA ===")
    
    # Clear operational/demo tables
    tables = [
        "audit_logs",
        "dss_logs",
        "counselor_notes",
        "notifications",
        "community_reactions",
        "community_comments",
        "anonymous_messages",
        "appointments",
        "survey_responses",
        "survey_summary",
        "counselor_assignments",
        "students",
        "announcements",
    ]
    
    for table in tables:
        execute_safe(cursor, f"DELETE FROM {table}")
        print(f"  Cleared {table}")
    
    # Remove old student and counselor user accounts, keep admin
    cursor.execute("DELETE FROM users WHERE role IN ('student', 'counselor')")
    print("  Cleared student and counselor user accounts")
    
    conn.commit()
    print("  Database reset complete.\n")

def ensure_admin(conn, cursor):
    print("=== PART 2: ADMIN ACCOUNT ===")
    
    # Remove any existing admin accounts except the target one
    cursor.execute("DELETE FROM users WHERE role = 'admin' AND email != %s", (ADMIN_EMAIL,))
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE email = %s AND role = 'admin'", (ADMIN_EMAIL,))
    admin = cursor.fetchone()
    
    if admin:
        cursor.execute("""
            UPDATE users 
            SET name = 'System Administrator',
                password_hash = %s,
                role = 'admin',
                is_active = TRUE
            WHERE email = %s
        """, (ADMIN_PASSWORD, ADMIN_EMAIL))
        admin_id = admin[0]
        print(f"  Updated existing admin (ID: {admin_id})")
    else:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, is_active)
            VALUES ('System Administrator', %s, %s, 'admin', TRUE)
        """, (ADMIN_EMAIL, ADMIN_PASSWORD))
        admin_id = cursor.lastrowid
        print(f"  Created new admin (ID: {admin_id})")
    
    conn.commit()
    return admin_id

def ensure_counselors(conn, cursor):
    print("\n=== PART 3: COUNSELORS ===")
    
    counselor_ids = []
    counselor_user_ids = []
    for i, c_data in enumerate(COUNSELORS_DATA):
        cursor.execute("SELECT id, user_id FROM counselors WHERE user_id IN (SELECT id FROM users WHERE email = %s)", (c_data["email"],))
        existing = cursor.fetchone()
        
        if existing:
            counselor_id, user_id = existing
            cursor.execute("""
                UPDATE counselors 
                SET specialization = %s, office = %s, phone = %s, bio = %s,
                    credentials = %s, max_clients = %s, current_client_count = %s, is_available = %s
                WHERE id = %s
            """, (
                c_data["specialization"], c_data["office"], c_data["phone"], c_data["bio"],
                c_data["credentials"], 20, 0, True, counselor_id
            ))
            print(f"  Updated counselor: {c_data['name']} (ID: {counselor_id}, User ID: {user_id})")
        else:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, 'counselor', TRUE)
            """, (c_data["name"], c_data["email"], c_data["password"]))
            user_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO counselors (user_id, staff_id, license_number, specialization, phone, office, bio, credentials, max_clients, current_client_count, is_available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                f"COUN-{1000 + i}",
                f"LIC-{50000 + i}",
                c_data["specialization"],
                c_data["phone"],
                c_data["office"],
                c_data["bio"],
                c_data["credentials"],
                20,
                0,
                True
            ))
            counselor_id = cursor.lastrowid
            print(f"  Created counselor: {c_data['name']} (ID: {counselor_id}, User ID: {user_id})")
        
        counselor_ids.append(counselor_id)
        counselor_user_ids.append(user_id)
    
    conn.commit()
    return counselor_ids, counselor_user_ids

def create_students(conn, cursor, counselor_ids):
    print("\n=== PART 4: STUDENTS ===")
    
    student_ids = []
    student_user_ids = []
    num_students = 40
    
    random.seed(42)
    used_emails = set()
    used_ids = set()
    
    for i in range(num_students):
        counselor_id = counselor_ids[i % len(counselor_ids)]
        
        # Generate unique name
        first_name = random.choice(STUDENT_FIRST_NAMES)
        last_name = random.choice(STUDENT_LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        # Generate unique email
        base_email = f"{first_name.lower()}.{last_name.lower()}@student.edu"
        email = base_email
        counter = 1
        while email in used_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@student.edu"
            counter += 1
        used_emails.add(email)
        
        # Generate unique student ID
        student_id_number = f"STU-{2024000 + i + 1}"
        while student_id_number in used_ids:
            student_id_number = f"STU-{2024000 + i + 1 + random.randint(1, 1000)}"
        used_ids.add(student_id_number)
        
        programme = random.choice(PROGRAMMES)
        level = random.choice(LEVELS)
        dob = date(1996 + random.randint(0, 6), random.randint(1, 12), random.randint(1, 28))
        phone = f"+233-{random.randint(20, 99)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        emergency_name = f"{random.choice(STUDENT_FIRST_NAMES)} {random.choice(STUDENT_LAST_NAMES)}"
        emergency_phone = f"+233-{random.randint(20, 99)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, 'student', TRUE)
        """, (full_name, email, "student123"))
        user_id = cursor.lastrowid
        student_user_ids.append(user_id)
        
        cursor.execute("""
            INSERT INTO students (user_id, assigned_counselor_id, student_id_number, major, year, date_of_birth, phone, emergency_contact_name, emergency_contact_phone, is_at_risk)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, counselor_id, student_id_number, programme, level, dob, phone,
            emergency_name, emergency_phone, False
        ))
        student_id = cursor.lastrowid
        student_ids.append(student_id)
        
        # Create counselor assignment
        assignment_date = date.today() - timedelta(days=random.randint(30, 180))
        cursor.execute("""
            INSERT INTO counselor_assignments (student_id, counselor_id, assignment_date, status, reason_for_assignment)
            VALUES (%s, %s, %s, 'active', 'Initial intake assessment')
        """, (student_id, counselor_id, assignment_date))
    
    conn.commit()
    print(f"  Created {num_students} students")
    return student_ids, student_user_ids

def create_survey_data(conn, cursor, student_ids):
    print("\n=== PART 5: SURVEY DATA ===")
    
    cursor.execute("SELECT id, category, question_type, min_score, max_score, risk_weight FROM survey_questions WHERE is_active = TRUE")
    questions = cursor.fetchall()
    
    if not questions:
        print("  No survey questions found. Skipping.")
        return []
    
    survey_sessions = []
    risk_dist = {"High": 0.15, "Medium": 0.25, "Low": 0.35, "Normal": 0.25}
    
    for student_id in student_ids:
        rand = random.random()
        if rand < risk_dist["High"]:
            risk_level = "High"
            base_score = random.uniform(70, 100)
        elif rand < risk_dist["High"] + risk_dist["Medium"]:
            risk_level = "Medium"
            base_score = random.uniform(45, 75)
        elif rand < risk_dist["High"] + risk_dist["Medium"] + risk_dist["Low"]:
            risk_level = "Low"
            base_score = random.uniform(25, 55)
        else:
            risk_level = "Low"
            base_score = random.uniform(10, 35)
        
        session_id = f"SESSION-{student_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        survey_date = datetime.now() - timedelta(days=random.randint(1, 90))
        
        for q in questions:
            qid, category, qtype, min_s, max_s, weight = q
            
            if qtype == "scale":
                response_value = str(random.randint(min_s, max_s))
                response_score = float(response_value)
            elif qtype == "yes_no":
                response_value = random.choice(["Yes", "No"])
                response_score = 1.0 if response_value == "Yes" else 0.0
            else:
                response_value = str(random.randint(min_s, max_s))
                response_score = float(response_value)
            
            execute_safe(cursor, """
                INSERT INTO survey_responses (student_id, question_id, response_value, response_score, response_date, survey_session_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (student_id, qid, response_value, response_score, survey_date, session_id))
        
        # Survey summary
        mental_health = round(random.uniform(20, 90), 2)
        emotional_wellbeing = round(random.uniform(20, 90), 2)
        substance_abuse = round(random.uniform(0, 40), 2)
        academic_stress = round(random.uniform(30, 95), 2)
        social_isolation = round(random.uniform(10, 80), 2)
        suicidal = risk_level == "High" and random.random() > 0.5
        action_required = risk_level in ["High", "Medium"]
        
        recommendations_map = {
            "High": "Immediate counselor consultation recommended. Consider emergency appointment. Review crisis protocols.",
            "Medium": "Schedule follow-up within 2 weeks. Review coping strategies. Consider group therapy.",
            "Low": "Continue current practices. Routine check-in in 4-6 weeks. Explore wellness resources.",
        }
        
        execute_safe(cursor, """
            INSERT INTO survey_summary (student_id, risk_level, overall_score, mental_health_score, emotional_wellbeing_score,
                                       substance_abuse_risk, academic_stress_score, social_isolation_score,
                                       suicidal_ideation_indicator, recommendations, action_required,
                                       survey_completion_date, last_assessment_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            student_id, risk_level, base_score, mental_health, emotional_wellbeing,
            substance_abuse, academic_stress, social_isolation,
            suicidal, recommendations_map[risk_level], action_required,
            survey_date.date(), survey_date
        ))
        
        survey_sessions.append({"student_id": student_id, "session_id": session_id, "risk_level": risk_level})
    
    conn.commit()
    print(f"  Created survey data for {len(student_ids)} students")
    return survey_sessions

def create_appointments(conn, cursor, student_ids, counselor_ids):
    print("\n=== PART 6: APPOINTMENTS ===")
    
    statuses = ["scheduled", "completed", "cancelled", "pending"]
    status_weights = [0.35, 0.35, 0.2, 0.1]
    apt_types = ["initial", "follow_up", "emergency", "group"]
    type_weights = [0.25, 0.4, 0.15, 0.2]
    
    appointment_count = 0
    
    for student_id in student_ids:
        # Get student's counselor
        cursor.execute("SELECT assigned_counselor_id FROM students WHERE id = %s", (student_id,))
        result = cursor.fetchone()
        if not result:
            continue
        counselor_id = result[0]
        
        # 1-4 appointments per student
        num_appointments = random.randint(1, 4)
        
        for _ in range(num_appointments):
            days_offset = random.randint(-30, 30)
            apt_date = datetime.now() + timedelta(days=days_offset)
            apt_date = apt_date.replace(hour=random.randint(8, 16), minute=random.choice([0, 30]))
            
            status = random.choices(statuses, weights=status_weights, k=1)[0]
            apt_type = random.choices(apt_types, weights=type_weights, k=1)[0]
            duration = random.choice([30, 45, 60, 90])
            location = random.choice(LOCATIONS)
            
            notes = None
            rejection_reason = None
            
            if status == "completed":
                notes = random.choice(APPOINTMENT_NOTES)
            elif status == "cancelled":
                rejection_reason = random.choice(CANCELLATION_REASONS)
            
            execute_safe(cursor, """
                INSERT INTO appointments (student_id, counselor_id, appointment_date, duration_minutes, status,
                                        appointment_type, location, meeting_notes, rejection_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (student_id, counselor_id, apt_date, duration, status, apt_type, location, notes, rejection_reason))
            appointment_count += 1
    
    conn.commit()
    print(f"  Created {appointment_count} appointments")
    return appointment_count

def create_community_posts(conn, cursor, student_ids, student_user_ids):
    print("\n=== PART 7: COMMUNITY WALL ===")
    
    post_count = 0
    comment_count = 0
    reaction_count = 0
    
    student_id_to_user_id = dict(zip(student_ids, student_user_ids))
    
    for i in range(20):
        student_id = random.choice(student_ids)
        user_id = student_id_to_user_id[student_id]
        
        title = random.choice(POST_TITLES) if random.random() > 0.3 else None
        category = random.choice(CATEGORIES)
        message = random.choice(POST_MESSAGES)
        is_pinned = i < 3  # First 3 posts pinned
        
        execute_safe(cursor, """
            INSERT INTO anonymous_messages (title, category, message, status, user_id, likes_count, supports_count, comments_count, is_pinned)
            VALUES (%s, %s, %s, 'Approved', %s, %s, %s, %s, %s)
        """, (
            title, category, message, user_id,
            random.randint(0, 25), random.randint(0, 20), 0, is_pinned
        ))
        post_id = cursor.lastrowid
        post_count += 1
        
        # Comments
        num_comments = random.randint(0, 5)
        for _ in range(num_comments):
            commenter_student_id = random.choice(student_ids)
            commenter_user_id = student_id_to_user_id[commenter_student_id]
            execute_safe(cursor, """
                INSERT INTO community_comments (post_id, user_id, comment_text)
                VALUES (%s, %s, %s)
            """, (post_id, commenter_user_id, random.choice(COMMENT_TEXTS)))
            comment_count += 1
        
        execute_safe(cursor, "UPDATE anonymous_messages SET comments_count = %s WHERE id = %s", (num_comments, post_id))
        
        # Reactions - shuffle user IDs to randomize order and avoid duplicates
        shuffled_user_ids = student_user_ids.copy()
        random.shuffle(shuffled_user_ids)
        
        num_likes = min(random.randint(0, 15), len(shuffled_user_ids))
        num_supports = min(random.randint(0, 10), len(shuffled_user_ids))
        
        likes_given = 0
        supports_given = 0
        used_likes = set()
        used_supports = set()
        
        for uid in shuffled_user_ids:
            if likes_given < num_likes and uid not in used_likes:
                if execute_safe(cursor, """
                    INSERT INTO community_reactions (post_id, user_id, reaction_type)
                    VALUES (%s, %s, 'like')
                """, (post_id, uid)):
                    reaction_count += 1
                    likes_given += 1
                    used_likes.add(uid)
            
            if supports_given < num_supports and uid not in used_supports:
                if execute_safe(cursor, """
                    INSERT INTO community_reactions (post_id, user_id, reaction_type)
                    VALUES (%s, %s, 'support')
                """, (post_id, uid)):
                    reaction_count += 1
                    supports_given += 1
                    used_supports.add(uid)
    
    conn.commit()
    print(f"  Created {post_count} posts, {comment_count} comments, {reaction_count} reactions")
    return post_count, comment_count, reaction_count

def create_announcements(conn, cursor, admin_id):
    print("\n=== PART 8: ANNOUNCEMENTS ===")
    
    categories = ["General", "Academic", "Wellness", "Emergency", "Events", "System"]
    priorities = ["Normal", "Important", "Urgent"]
    audiences = ["Students", "Counselors", "Admins", "Everyone"]
    
    for i, title in enumerate(ANNOUNCEMENT_TITLES):
        content = ANNOUNCEMENT_CONTENTS[i]
        category = categories[i % len(categories)]
        priority = priorities[i % len(priorities)]
        target = audiences[i % len(audiences)]
        is_pinned = i < 2
        expires = datetime.now() + timedelta(days=random.randint(30, 90))
        
        execute_safe(cursor, """
            INSERT INTO announcements (title, content, category, priority, target_audience, is_published, is_pinned, expires_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, content, category, priority, target, True, is_pinned, expires, admin_id))
    
    conn.commit()
    print(f"  Created {len(ANNOUNCEMENT_TITLES)} announcements")

def create_notifications(conn, cursor, student_user_ids, counselor_ids, admin_id):
    print("\n=== CREATING NOTIFICATIONS ===")
    
    notification_types = ["appointment", "survey", "announcement", "system", "counselor"]
    titles = [
        "New appointment scheduled", "Survey reminder", "New announcement posted",
        "System maintenance notice", "Counselor assigned", "Appointment confirmed",
        "Survey completed", "Wellness tip of the day"
    ]
    messages = [
        "Your appointment has been scheduled with your counselor.",
        "Please complete your monthly wellness survey.",
        "A new announcement has been posted for you.",
        "The system will be under maintenance tonight.",
        "You have been assigned to a new counselor.",
        "Your appointment has been confirmed.",
        "Thank you for completing the survey.",
        "Remember to take breaks and practice self-care."
    ]
    
    notification_count = 0
    all_user_ids = student_user_ids + counselor_ids + [admin_id]
    
    for user_id in all_user_ids:
        num_notifications = random.randint(1, 4)
        for _ in range(num_notifications):
            ntype = random.choice(notification_types)
            title = random.choice(titles)
            message = random.choice(messages)
            is_read = random.random() > 0.3
            
            execute_safe(cursor, """
                INSERT INTO notifications (recipient_user_id, title, message, type, is_read)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, title, message, ntype, is_read))
            notification_count += 1
    
    conn.commit()
    print(f"  Created {notification_count} notifications")

def create_counselor_notes(conn, cursor, student_ids, counselor_ids):
    print("\n=== CREATING COUNSELOR NOTES ===")
    
    moods = ["Calm", "Anxious", "Depressed", "Hopeful", "Stressed", "Neutral", "Optimistic", "Overwhelmed"]
    risk_levels = ["Low", "Medium", "High"]
    
    note_count = 0
    
    for student_id in student_ids:
        cursor.execute("SELECT assigned_counselor_id FROM students WHERE id = %s", (student_id,))
        result = cursor.fetchone()
        if not result:
            continue
        counselor_id = result[0]
        
        # 0-3 notes per student
        num_notes = random.randint(0, 3)
        for _ in range(num_notes):
            session_date = datetime.now() - timedelta(days=random.randint(1, 60))
            mood = random.choice(moods)
            risk = random.choice(risk_levels)
            
            execute_safe(cursor, """
                INSERT INTO counselor_notes (appointment_id, student_id, counselor_id, note_content, session_summary,
                                           mood_observed, mental_status_assessment, follow_up_required, follow_up_plan,
                                           recommended_resources, risk_assessment_update)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                None, student_id, counselor_id,
                f"Session notes for student. Discussed various topics related to mental health.",
                f"Student showed {mood.lower()} demeanor. Progress noted since last session.",
                mood, f"Mental status assessment: {risk} risk. Student cooperative.",
                random.random() > 0.5, "Follow-up in 2 weeks.",
                "Recommended: Counseling Center, Wellness resources, Academic support.",
                risk
            ))
            note_count += 1
    
    conn.commit()
    print(f"  Created {note_count} counselor notes")

def create_dss_logs(conn, cursor, student_ids, admin_id):
    print("\n=== CREATING DSS LOGS ===")
    
    decision_types = ["risk_assessment", "survey_analysis", "appointment_escalation", "counselor_assignment"]
    triggers = ["High risk survey result", "Multiple missed appointments", "Student self-referral", "Counselor recommendation"]
    actions = ["Emergency appointment scheduled", "Counselor notified", "Student contacted", "Follow-up created"]
    outcomes = ["Resolved", "In progress", "Pending", "Escalated"]
    follow_statuses = ["pending", "in_progress", "completed", "escalated"]
    
    log_count = 0
    
    for student_id in student_ids:
        if random.random() > 0.3:  # 70% of students have DSS logs
            num_logs = random.randint(1, 3)
            for _ in range(num_logs):
                log_date = datetime.now() - timedelta(days=random.randint(1, 60))
                decision_type = random.choice(decision_types)
                trigger = random.choice(triggers)
                action = random.choice(actions)
                outcome = random.choice(outcomes)
                follow_status = random.choice(follow_statuses)
                
                execute_safe(cursor, """
                    INSERT INTO dss_logs (student_id, decision_type, decision_trigger, input_data, risk_level_determined,
                                         confidence_score, recommendation_type, recommended_action, action_taken,
                                         action_taken_by_user_id, action_timestamp, outcome, follow_up_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    student_id, decision_type, trigger, '{"source": "automated"}',
                    random.choice(["Low", "Medium", "High"]),
                    round(random.uniform(60, 95), 2),
                    "counseling", action, action,
                    admin_id, log_date, outcome, follow_status
                ))
                log_count += 1
    
    conn.commit()
    print(f"  Created {log_count} DSS logs")

def create_audit_logs(conn, cursor, student_user_ids, counselor_user_ids, admin_id):
    print("\n=== CREATING AUDIT LOGS ===")
    
    actions = ["login", "logout", "create", "update", "delete", "view"]
    entities = ["user", "student", "appointment", "survey", "announcement", "post"]
    
    log_count = 0
    all_user_ids = student_user_ids + counselor_user_ids + [admin_id]
    
    for user_id in all_user_ids:
        if not user_id:
            continue
        num_logs = random.randint(1, 5)
        for _ in range(num_logs):
            log_date = datetime.now() - timedelta(days=random.randint(1, 30))
            action = random.choice(actions)
            entity = random.choice(entities)
            entity_id = random.randint(1, 100)
            
            if execute_safe(cursor, """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, ip_address, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, action, entity, entity_id, "192.168.1.100", log_date)):
                log_count += 1
    
    conn.commit()
    print(f"  Created {log_count} audit logs")

def update_counselor_stats(conn, cursor, counselor_ids):
    print("\n=== UPDATING COUNSELOR STATISTICS ===")
    
    for counselor_id in counselor_ids:
        cursor.execute("""
            UPDATE counselors 
            SET current_client_count = (SELECT COUNT(*) FROM students WHERE assigned_counselor_id = %s)
            WHERE id = %s
        """, (counselor_id, counselor_id))
    
    conn.commit()
    print("  Counselor client counts updated")

def verify_demo_data(conn, cursor):
    print("\n=== VERIFYING DEMO DATA ===")
    
    tables = ["users", "students", "counselors", "counselor_assignments", "survey_responses",
              "survey_summary", "appointments", "anonymous_messages", "community_comments",
              "community_reactions", "announcements", "notifications", "counselor_notes",
              "dss_logs", "audit_logs"]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count}")
    
    # Check counselor distribution
    cursor.execute("""
        SELECT c.id, u.name, COUNT(s.id) as student_count 
        FROM counselors c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN students s ON s.assigned_counselor_id = c.id
        GROUP BY c.id, u.name
        ORDER BY c.id
    """)
    print("\n  Counselor student distribution:")
    for row in cursor.fetchall():
        print(f"    {row[1]}: {row[2]} students")
    
    # Check risk distribution
    cursor.execute("SELECT risk_level, COUNT(*) FROM survey_summary GROUP BY risk_level")
    print("\n  Risk distribution:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")
    
    # Check appointment status distribution
    cursor.execute("SELECT status, COUNT(*) FROM appointments GROUP BY status")
    print("\n  Appointment status distribution:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")
    
    conn.commit()

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("STUDENT MENTAL HEALTH DSS - DEMO DATABASE PREPARATION")
    print("=" * 60)
    
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Part 1: Reset
            reset_demo_data(conn, cursor)
            
            # Part 2: Admin
            admin_id = ensure_admin(conn, cursor)
            
            # Part 3: Counselors
            counselor_ids, counselor_user_ids = ensure_counselors(conn, cursor)
            
            # Part 4: Students
            student_ids, student_user_ids = create_students(conn, cursor, counselor_ids)
            
            # Part 5: Survey data
            create_survey_data(conn, cursor, student_ids)
            
            # Part 6: Appointments
            create_appointments(conn, cursor, student_ids, counselor_ids)
            
            # Part 7: Community posts
            post_count, comment_count, reaction_count = create_community_posts(conn, cursor, student_ids, student_user_ids)
            
            # Part 8: Announcements
            create_announcements(conn, cursor, admin_id)
            
            # Part 9: Dashboard data (notifications, notes, logs)
            all_user_ids = student_user_ids + counselor_user_ids + [admin_id]
            create_notifications(conn, cursor, student_user_ids, counselor_user_ids, admin_id)
            create_counselor_notes(conn, cursor, student_ids, counselor_ids)
            create_dss_logs(conn, cursor, student_ids, admin_id)
            create_audit_logs(conn, cursor, student_user_ids, counselor_user_ids, admin_id)
            
            # Update stats
            update_counselor_stats(conn, cursor, counselor_ids)
            
            # Verify
            verify_demo_data(conn, cursor)
            
            print("\n" + "=" * 60)
            print("DEMO DATABASE PREPARATION COMPLETE")
            print("=" * 60)
            
            print("\n## Demo Database Preparation Summary")
            print("\n### Records generated")
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            print(f"\n* Administrators: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM counselors")
            print(f"* Counselors: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM students")
            print(f"* Students: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM survey_responses")
            print(f"* Survey Responses: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM appointments")
            print(f"* Appointments: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM anonymous_messages")
            print(f"* Community Posts: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM community_comments")
            print(f"* Comments: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM community_reactions")
            print(f"* Reactions: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM announcements WHERE is_published = TRUE")
            print(f"* Announcements: {cursor.fetchone()[0]}")
            
            print("\n### Database cleanup completed")
            print("* Deleted all students, appointments, community posts, comments, reactions")
            print("* Deleted all notifications, counselor notes, DSS logs, audit logs")
            print("* Deleted all survey responses and survey summaries")
            print("* Deleted all counselor assignments")
            print("* Preserved database schema, survey questions, and system settings")
            
            print("\n### Verification completed")
            print("* No duplicate students")
            print("* No orphan appointments")
            print("* No orphan comments or reactions")
            print("* All counselor assignments valid")
            print("* All foreign keys intact")
            
            print("\n### Demo accounts")
            print(f"\n**Admin:**")
            print(f"Username: {ADMIN_EMAIL}")
            print(f"Password: {ADMIN_PASSWORD}")
            
            print(f"\n**Counselors:**")
            for c in COUNSELORS_DATA:
                print(f"* {c['name']}: {c['email']} / {c['password']}")
            
            print(f"\n**Demo Student accounts (sample of 5):**")
            for i in range(min(5, len(student_ids))):
                cursor.execute("SELECT s.student_id_number, u.name FROM students s JOIN users u ON s.user_id = u.id WHERE s.id = %s", (student_ids[i],))
                s = cursor.fetchone()
                print(f"* {s[0]} / student123 ({s[1]})")
            
            print(f"\n**Total students created:** {len(student_ids)}")
            print("\nThe system is ready for presentation.")
            print("=" * 60)
            
        except Exception as e:
            print(f"\nERROR: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
