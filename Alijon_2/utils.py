from datetime import datetime, date
from models import db, Student, Group, Attendance
from sqlalchemy import func

def get_current_datetime():
    """Hozirgi sana va vaqtni olish"""
    return datetime.now()

def get_current_date():
    """Hozirgi sanani olish"""
    return date.today()

def get_or_create_group(group_name):
    """Guruhni olish yoki yangi yaratish"""
    group_name = group_name.strip()
    group = Group.query.filter_by(name=group_name).first()
    
    if not group:
        group = Group(name=group_name)
        db.session.add(group)
        db.session.commit()
    
    return group

def update_group_access(group_id):
    """Guruhga kirish vaqti va sanagini yangilash"""
    group = Group.query.get(group_id)
    if group:
        group.last_accessed = datetime.utcnow()
        group.access_count += 1
        db.session.commit()

def get_students_alphabetically(group_id):
    """Guruh talabalarini alfabit tartibida olish"""
    return Student.query.filter_by(group_id=group_id).order_by(
        Student.last_name,
        Student.first_name,
        Student.patronymic
    ).all()

def get_or_create_attendance(student_id, target_date):
    """Davomat yozuvini olish yoki yaratish"""
    attendance = Attendance.query.filter_by(
        student_id=student_id,
        date=target_date
    ).first()
    
    if not attendance:
        student = Student.query.get(student_id)
        attendance = Attendance(
            student_id=student_id,
            group_id=student.group_id,
            date=target_date
        )
        db.session.add(attendance)
        db.session.commit()
    
    return attendance

def calculate_total_absences(student_id):
    """Talabaning jami g'oyiblarini hisoblash"""
    records = Attendance.query.filter_by(student_id=student_id).all()
    total = 0
    for record in records:
        total += record.count_absent()
    return total

def get_student_attendance_history(student_id):
    """Talabaning to'liq davom tarixi"""
    return Attendance.query.filter_by(student_id=student_id).order_by(
        Attendance.date.desc()
    ).all()

def get_dashboard_stats():
    """Dashboard uchun statistika"""
    total_students = Student.query.count()
    total_groups = Group.query.count()
    
    # Bugungi davomat statistikasi
    today = get_current_date()
    today_attendance = Attendance.query.filter_by(date=today).all()
    
    present = 0
    absent = 0
    
    for att in today_attendance:
        present += att.count_present()
        absent += att.count_absent()
    
    total_checked = present + absent
    present_percentage = (present / total_checked * 100) if total_checked > 0 else 0
    
    return {
        'total_students': total_students,
        'total_groups': total_groups,
        'present_today': present,
        'absent_today': absent,
        'present_percentage': round(present_percentage, 1),
        'current_datetime': get_current_datetime()
    }
