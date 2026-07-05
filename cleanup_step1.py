import sys
sys.path.insert(0, '.')
from database import get_connection

conn = get_connection()
cursor = conn.cursor()

try:
    # Start transaction for safety
    conn.start_transaction()

    # Student user IDs to remove (all except admin 2 and counselor 3)
    student_user_ids = (1, 4, 8, 10, 11, 12)
    # Corresponding student IDs from students table
    student_ids = (1, 2, 4, 6, 7, 8)

    print('=== CLEANUP START ===')

    # 1. Delete counselor notes tied to deleted students
    print('Deleting counselor_notes for students...')
    cursor.execute(
        'DELETE FROM counselor_notes WHERE student_id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  counselor_notes deleted:', cursor.rowcount)

    # 2. Delete appointments tied to deleted students
    print('Deleting appointments for students...')
    cursor.execute(
        'DELETE FROM appointments WHERE student_id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  appointments deleted:', cursor.rowcount)

    # 3. Delete counselor assignments tied to deleted students
    print('Deleting counselor_assignments for students...')
    cursor.execute(
        'DELETE FROM counselor_assignments WHERE student_id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  counselor_assignments deleted:', cursor.rowcount)

    # 4. Delete survey responses for deleted students
    print('Deleting survey_responses for students...')
    cursor.execute(
        'DELETE FROM survey_responses WHERE student_id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  survey_responses deleted:', cursor.rowcount)

    # 5. Delete survey summaries for deleted students
    print('Deleting survey_summary for students...')
    cursor.execute(
        'DELETE FROM survey_summary WHERE student_id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  survey_summary deleted:', cursor.rowcount)

    # 6. Delete dss_logs for deleted students
    print('Deleting dss_logs for students...')
    cursor.execute(
        'DELETE FROM dss_logs WHERE student_id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  dss_logs deleted:', cursor.rowcount)

    # 7. Delete students records
    print('Deleting students...')
    cursor.execute(
        'DELETE FROM students WHERE id IN (%s)' % ','.join(map(str, student_ids))
    )
    print('  students deleted:', cursor.rowcount)

    # 8. Delete student user accounts
    print('Deleting student user accounts...')
    cursor.execute(
        'DELETE FROM users WHERE id IN (%s)' % ','.join(map(str, student_user_ids))
    )
    print('  users deleted:', cursor.rowcount)

    conn.commit()
    print('\n=== CLEANUP COMMITTED ===')

except Exception as e:
    conn.rollback()
    print('ERROR - rolled back:', e)
    raise
finally:
    cursor.close()
    conn.close()

print('\n=== VERIFICATION ===')
conn = get_connection()
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM users')
print('users:', cursor.fetchone()[0])
cursor.execute('SELECT id, name, email, role FROM users ORDER BY role, id')
print('users detail:', cursor.fetchall())

cursor.execute('SELECT COUNT(*) FROM students')
print('students:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM counselors')
print('counselors:', cursor.fetchone()[0])
cursor.execute('SELECT id, user_id FROM counselors')
print('counselors detail:', cursor.fetchall())

cursor.execute('SELECT COUNT(*) FROM appointments')
print('appointments:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM counselor_assignments')
print('counselor_assignments:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM survey_responses')
print('survey_responses:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM survey_summary')
print('survey_summary:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM counselor_notes')
print('counselor_notes:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM dss_logs')
print('dss_logs:', cursor.fetchone()[0])

cursor.close()
conn.close()
