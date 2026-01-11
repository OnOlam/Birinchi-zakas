"""
Flask Application - Attendance Management System
Davomatni boshqarish tizimi - Asosiy fayl
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session,make_response, jsonify
from datetime import datetime, timedelta
import os

# O'zimizning modullari
from models import db, init_db, Group, Student, Attendance
from auth import (
    check_login, login_user, logout_user, 
    login_required, is_logged_in, init_auth
)
from config import get_config

# ==========================================
# FLASK APP SOZLAMALARI
# ==========================================

def create_app(config_name=None):
    """
    Flask Application Factory
    
    Args:
        config_name: 'development', 'production', or 'testing'
    
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize extensions
    init_db(app)
    init_auth(app)
    
    # Register blueprints (agar kerak bo'lsa)
    # register_blueprints(app)
    
    return app


# Create app instance
app = create_app()


# ==========================================
# BEFORE FIRST REQUEST
# ==========================================

@app.before_request
def create_tables():
    """
    Create database tables before first request
    """
    db.create_all()


# ==========================================
# JINJA FILTERS (Optional)
# ==========================================

@app.template_filter('format_date')
def format_date_filter(date, format='%d.%m.%Y'):
    """Format date for templates"""
    if date:
        return date.strftime(format)
    return ''


# ==========================================
# HOME PAGE & LOGIN
# ==========================================

@app.route('/')
def index():
    """
    Bosh sahifa - agar login qilgan bo'lsa dashboard'ga yo'naltirish
    """
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login sahifasi - Secure token-based authentication
    GET: Login formani ko'rsatish
    POST: Login ma'lumotlarini tekshirish
    """
    from auth import (
        try_auto_login, get_client_info, 
        create_remember_me_token, rate_limit_check
    )
    
    # Auto-login tekshirish (cookie orqali)
    if try_auto_login():
        return redirect(url_for('dashboard'))
    
    # Agar session orqali login qilgan bo'lsa
    if is_logged_in():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Rate limiting tekshirish
        if not rate_limit_check():
            flash('Juda ko\'p urinish! Iltimos biroz kutib turing. ⏳', 'danger')
            return render_template('login.html')
        
        # Login tekshirish
        if check_login(username, password):
            # Session yaratish
            login_user(username, login_method='password')
            
            # Redirect response yaratish
            next_url = session.pop('next_url', None)
            response = make_response(redirect(next_url or url_for('dashboard')))
            
            # "Remember Me" token yaratish
            if remember_me:
                user_agent, ip_address = get_client_info()
                response = create_remember_me_token(
                    response,
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                flash('Xush kelibsiz! Qurilma eslab qolindi. 🔐', 'success')
            else:
                flash('Xush kelibsiz! 👋', 'success')
            
            return response
        else:
            flash('Username yoki parol noto\'g\'ri! ❌', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """
    Logout - tizimdan chiqish va tokenni bekor qilish
    """
    from auth import revoke_remember_me_token
    
    username = session.get('username')
    
    # Session tozalash
    logout_user()
    
    # Response yaratish
    response = make_response(redirect(url_for('login')))
    
    # Remember me tokenni bekor qilish
    response = revoke_remember_me_token(response)
    
    flash(f'{username}, tizimdan muvaffaqiyatli chiqdingiz! 👋', 'info')
    
    return response


# ==========================================
# DASHBOARD (Asosiy sahifa)
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard - Asosiy boshqaruv paneli
    Bugungi davomatning to'liq statistikasi
    """
    # Bugungi sana
    today = datetime.now().date()
    
    # Sana formatlash
    uzbek_weekdays = {
        0: 'Dushanba',
        1: 'Seshanba',
        2: 'Chorshanba',
        3: 'Payshanba',
        4: 'Juma',
        5: 'Shanba',
        6: 'Yakshanba'
    }
    
    uzbek_months = {
        1: 'Yanvar',
        2: 'Fevral',
        3: 'Mart',
        4: 'Aprel',
        5: 'May',
        6: 'Iyun',
        7: 'Iyul',
        8: 'Avgust',
        9: 'Sentabr',
        10: 'Oktabr',
        11: 'Noyabr',
        12: 'Dekabr'
    }
    
    weekday = uzbek_weekdays[today.weekday()]
    today_formatted = f"{today.day} {uzbek_months[today.month]}, {today.year}"
    
    # Bugungi davomat statistikasi
    today_attendance = Attendance.query.filter_by(date=today).all()
    
    total_present = len([a for a in today_attendance if a.status == 'present'])
    total_absent = len([a for a in today_attendance if a.status == 'absent'])
    total_records = len(today_attendance)
    
    # Foizni hisoblash
    if total_records > 0:
        percentage = round((total_present / total_records) * 100, 1)
    else:
        percentage = 0
    
    # Umumiy statistika
    total_students = Student.query.filter_by(active=True).count()
    total_groups = Group.query.count()
    
    today_stats = {
        'total': total_records,
        'present': total_present,
        'absent': total_absent,
        'percentage': percentage,
        'total_students': total_students,
        'total_groups': total_groups
    }
    
    return render_template('dashboard.html',
                         today_date=today_formatted,
                         today_weekday=weekday,
                         today_stats=today_stats)


# ==========================================
# ADMIN PANEL - GURUHLAR VA TALABALAR
# ==========================================

@app.route('/admin')
@login_required
def admin_panel():
    """
    Admin panel - Guruhlar va talabalarni boshqarish
    Bitta sahifada barcha CRUD operatsiyalar
    """
    # Barcha guruhlar (talabalar sonini hisoblab)
    groups = Group.query.all()
    groups_data = []
    for group in groups:
        active_students_count = Student.query.filter_by(
            group_id=group.id, 
            active=True
        ).count()
        groups_data.append({
            'group': group,
            'students_count': active_students_count
        })
    
    # Barcha aktiv talabalar
    students = Student.query.filter_by(active=True).order_by(
        Student.group_id, Student.first_name
    ).all()
    
    return render_template('admin_panel.html',
                         groups_data=groups_data,
                         students=students,
                         all_groups=groups)


# ==========================================
# GURUHLAR BOSHQARUVI
# ==========================================

@app.route('/admin/group/add', methods=['POST'])
@login_required
def add_group():
    """
    Yangi guruh qo'shish
    Validation: Nom bo'sh bo'lmasligi va takrorlanmasligi
    """
    name = request.form.get('name', '').strip()
    
    # Validation: Bo'sh nom
    if not name:
        flash('Guruh nomi bo\'sh bo\'lishi mumkin emas! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Validation: Nom uzunligi (3-100 belgi)
    if len(name) < 3:
        flash('Guruh nomi kamida 3 belgidan iborat bo\'lishi kerak! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    if len(name) > 100:
        flash('Guruh nomi 100 belgidan oshmasligi kerak! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Validation: Takroriy nom
    existing = Group.query.filter_by(name=name).first()
    if existing:
        flash(f'"{name}" nomli guruh allaqachon mavjud! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    try:
        # Yangi guruh qo'shish
        new_group = Group(name=name)
        db.session.add(new_group)
        db.session.commit()
        
        flash(f'✅ "{name}" guruhi muvaffaqiyatli qo\'shildi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/group/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    """
    Guruhni o'chirish
    MUHIM: Agar guruhda talabalar bo'lsa, o'chmasin!
    """
    group = Group.query.get_or_404(group_id)
    
    # Guruhda aktiv talabalar bormi tekshirish
    active_students_count = Student.query.filter_by(
        group_id=group_id, 
        active=True
    ).count()
    
    if active_students_count > 0:
        flash(
            f'❌ "{group.name}" guruhini o\'chirib bo\'lmaydi! '
            f'Guruhda {active_students_count} ta talaba mavjud. '
            f'Avval talabalarni boshqa guruhga o\'tkazing yoki o\'chiring.',
            'danger'
        )
        return redirect(url_for('admin_panel'))
    
    try:
        # Guruhni o'chirish
        db.session.delete(group)
        db.session.commit()
        
        flash(f'✅ "{group.name}" guruhi o\'chirildi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/group/<int:group_id>/edit', methods=['POST'])
@login_required
def edit_group(group_id):
    """
    Guruh nomini o'zgartirish
    """
    group = Group.query.get_or_404(group_id)
    new_name = request.form.get('name', '').strip()
    
    # Validation
    if not new_name:
        flash('Guruh nomi bo\'sh bo\'lishi mumkin emas! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    if len(new_name) < 3 or len(new_name) > 100:
        flash('Guruh nomi 3-100 belgi oralig\'ida bo\'lishi kerak! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Boshqa guruhda bunday nom bormi tekshirish
    existing = Group.query.filter(
        Group.name == new_name,
        Group.id != group_id
    ).first()
    
    if existing:
        flash(f'"{new_name}" nomli guruh allaqachon mavjud! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    try:
        old_name = group.name
        group.name = new_name
        db.session.commit()
        
        flash(f'✅ Guruh nomi "{old_name}" dan "{new_name}" ga o\'zgartirildi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


# ==========================================
# TALABALAR BOSHQARUVI
# ==========================================

@app.route('/admin/student/add', methods=['POST'])
@login_required
def add_student():
    """
    Yangi talaba qo'shish
    Validation: Ism, familiya va guruh majburiy
    """
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    group_id = request.form.get('group_id', type=int)
    
    # Validation: Bo'sh maydonlar
    if not first_name or not last_name:
        flash('Ism va familiya to\'ldirilishi shart! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Validation: Nom uzunligi (2-100 belgi)
    if len(first_name) < 2 or len(last_name) < 2:
        flash('Ism va familiya kamida 2 belgidan iborat bo\'lishi kerak! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    if len(first_name) > 100 or len(last_name) > 100:
        flash('Ism va familiya 100 belgidan oshmasligi kerak! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Validation: Guruh tanlangan
    if not group_id:
        flash('Guruh tanlanishi shart! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    # Validation: Guruh mavjudmi
    group = Group.query.get(group_id)
    if not group:
        flash('Tanlangan guruh topilmadi! ❌', 'danger')
        return redirect(url_for('admin_panel'))
    
    try:
        # Yangi talaba qo'shish
        new_student = Student(
            first_name=first_name,
            last_name=last_name,
            group_id=group_id,
            active=True
        )
        db.session.add(new_student)
        db.session.commit()
        
        flash(
            f'✅ {first_name} {last_name} ({group.name}) muvaffaqiyatli qo\'shildi!',
            'success'
        )
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    """
    Talabani o'chirish (SOFT DELETE)
    active = False qilinadi, database'dan o'chirilmaydi
    """
    student = Student.query.get_or_404(student_id)
    
    # Agar allaqachon o'chirilgan bo'lsa
    if not student.active:
        flash(f'{student.full_name} allaqachon o\'chirilgan! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    try:
        # Soft delete
        student.active = False
        db.session.commit()
        
        flash(f'✅ {student.full_name} o\'chirildi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/student/<int:student_id>/restore', methods=['POST'])
@login_required
def restore_student(student_id):
    """
    O'chirilgan talabani qayta tiklash
    """
    student = Student.query.get_or_404(student_id)
    
    if student.active:
        flash(f'{student.full_name} allaqachon aktiv! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    try:
        student.active = True
        db.session.commit()
        
        flash(f'✅ {student.full_name} qayta tiklandi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/student/<int:student_id>/edit', methods=['POST'])
@login_required
def edit_student(student_id):
    """
    Talaba ma'lumotlarini o'zgartirish
    """
    student = Student.query.get_or_404(student_id)
    
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    group_id = request.form.get('group_id', type=int)
    
    # Validation
    if not first_name or not last_name or not group_id:
        flash('Barcha maydonlar to\'ldirilishi shart! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    if len(first_name) < 2 or len(last_name) < 2:
        flash('Ism va familiya kamida 2 belgidan iborat bo\'lishi kerak! ⚠️', 'warning')
        return redirect(url_for('admin_panel'))
    
    try:
        student.first_name = first_name
        student.last_name = last_name
        student.group_id = group_id
        db.session.commit()
        
        flash(f'✅ {student.full_name} ma\'lumotlari yangilandi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Xatolik yuz berdi: {str(e)} ❌', 'danger')
    
    return redirect(url_for('admin_panel'))


# ==========================================
# O'CHIRILGAN TALABALAR RO'YXATI
# ==========================================

@app.route('/admin/deleted-students')
@login_required
def deleted_students():
    """
    O'chirilgan talabalar ro'yxati
    """
    deleted = Student.query.filter_by(active=False).all()
    return render_template('deleted_students.html', students=deleted)


# ==========================================
# DAVOMAT BELGILASH
# ==========================================

@app.route('/attendance')
@login_required
def attendance_page():
    """
    Davomat sahifasi - kunlik davomat belgilash
    """
    # Sanani olish (URL'dan yoki bugungi kun)
    date_str = request.args.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.now().date()
    
    # Guruhni tanlash
    group_id = request.args.get('group_id', type=int)
    
    # Talabalar ro'yxati (faqat aktiv)
    query = Student.query.filter_by(active=True)
    if group_id:
        query = query.filter_by(group_id=group_id)
    students = query.order_by(Student.first_name).all()
    
    # Har bir talabaning davomat holatini tekshirish
    attendance_data = []
    for student in students:
        att = Attendance.query.filter_by(
            student_id=student.id,
            date=selected_date
        ).first()
        
        attendance_data.append({
            'student': student,
            'status': att.status if att else None
        })
    
    groups = Group.query.all()
    
    return render_template('attendance.html',
                         attendance_data=attendance_data,
                         selected_date=selected_date,
                         groups=groups,
                         selected_group=group_id)


@app.route('/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    """
    Davomatni belgilash yoki yangilash
    AJAX request orqali
    """
    student_id = request.form.get('student_id', type=int)
    date_str = request.form.get('date')
    status = request.form.get('status')
    
    # Validation
    if not all([student_id, date_str, status]):
        return jsonify({
            'success': False, 
            'message': 'Ma\'lumotlar to\'liq emas'
        }), 400
    
    if status not in ['present', 'absent']:
        return jsonify({
            'success': False, 
            'message': 'Noto\'g\'ri status'
        }), 400
    
    try:
        # Sanani parse qilish
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Talaba mavjudligini tekshirish
        student = Student.query.get(student_id)
        if not student or not student.active:
            return jsonify({
                'success': False, 
                'message': 'Talaba topilmadi'
            }), 404
        
        # Davomatni belgilash yoki yangilash
        Attendance.mark_attendance(student_id, date, status)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'{student.full_name} - {status}',
            'student_name': student.full_name,
            'status': status
        })
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Noto\'g\'ri sana formati'
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Xatolik: {str(e)}'
        }), 500


@app.route('/attendance/bulk-mark', methods=['POST'])
@login_required
def bulk_mark_attendance():
    """
    Ko'p talabalarning davomatini bir vaqtda belgilash
    """
    try:
        data = request.get_json()
        date_str = data.get('date')
        attendances = data.get('attendances', [])
        
        if not date_str or not attendances:
            return jsonify({
                'success': False,
                'message': 'Ma\'lumotlar to\'liq emas'
            }), 400
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Har bir talabani belgilash
        saved_count = 0
        for item in attendances:
            student_id = item.get('student_id')
            status = item.get('status')
            
            if student_id and status in ['present', 'absent']:
                Attendance.mark_attendance(student_id, date, status)
                saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{saved_count} ta talaba davomati saqlandi',
            'count': saved_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==========================================
# HISOBOTLAR VA EXCEL EXPORT
# ==========================================

@app.route('/reports')
@login_required
def reports():
    """
    Hisobotlar sahifasi - sana tanlash
    """
    from datetime import date
    
    today = date.today()
    
    return render_template('reports.html',
                         selected_date=today.strftime('%Y-%m-%d'),
                         groups_report=None)


@app.route('/reports/view')
@login_required
def reports_view():
    """
    Tanlangan sana bo'yicha hisobotni ko'rsatish
    """
    date_str = request.args.get('date')
    
    if not date_str:
        flash('Iltimos sana tanlang! ⚠️', 'warning')
        return redirect(url_for('reports'))
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Noto\'g\'ri sana formati! ❌', 'danger')
        return redirect(url_for('reports'))
    
    # Barcha guruhlar bo'yicha hisobot
    groups = Group.query.all()
    groups_report = []
    
    for group in groups:
        # Guruhning o'sha sanada davomat ma'lumotlari
        students = Student.query.filter_by(
            group_id=group.id,
            active=True
        ).all()
        
        students_data = []
        present_count = 0
        absent_count = 0
        
        for student in students:
            # Talabaning o'sha sanada davomati
            attendance = Attendance.query.filter_by(
                student_id=student.id,
                date=selected_date
            ).first()
            
            status = None
            if attendance:
                status = attendance.status
                if status == 'present':
                    present_count += 1
                elif status == 'absent':
                    absent_count += 1
            
            students_data.append({
                'student_id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'status': status
            })
        
        total = len(students_data)
        percentage = (present_count / total * 100) if total > 0 else 0
        
        if total > 0:  # Faqat talabasi bor guruhlar
            groups_report.append({
                'group_id': group.id,
                'group_name': group.name,
                'students': students_data,
                'total': total,
                'present': present_count,
                'absent': absent_count,
                'percentage': round(percentage, 1)
            })
    
    return render_template('reports.html',
                         selected_date=date_str,
                         groups_report=groups_report)


@app.route('/reports/export')
@login_required
def reports_export():
    """
    Excel hisobotni yuklab olish
    """
    from flask import send_file
    from export import AttendanceExcelExporter, generate_filename
    
    date_str = request.args.get('date')
    group_id = request.args.get('group_id', type=int)
    
    if not date_str:
        flash('Iltimos sana tanlang! ⚠️', 'warning')
        return redirect(url_for('reports'))
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Noto\'g\'ri sana formati! ❌', 'danger')
        return redirect(url_for('reports'))
    
    exporter = AttendanceExcelExporter()
    
    # Agar muayyan guruh tanlangan bo'lsa
    if group_id:
        group = Group.query.get_or_404(group_id)
        
        # Guruh talabalarini olish
        students = Student.query.filter_by(
            group_id=group_id,
            active=True
        ).all()
        
        students_data = []
        for student in students:
            attendance = Attendance.query.filter_by(
                student_id=student.id,
                date=selected_date
            ).first()
            
            students_data.append({
                'first_name': student.first_name,
                'last_name': student.last_name,
                'status': attendance.status if attendance else None
            })
        
        # Excel yaratish
        excel_file = exporter.export_group_report(
            selected_date,
            group.name,
            students_data
        )
        
        filename = generate_filename('davomat', selected_date, group.name)
    
    else:
        # Barcha guruhlar uchun
        groups = Group.query.all()
        groups_data = []
        
        for group in groups:
            students = Student.query.filter_by(
                group_id=group.id,
                active=True
            ).all()
            
            if not students:
                continue
            
            students_data = []
            present_count = 0
            absent_count = 0
            
            for student in students:
                attendance = Attendance.query.filter_by(
                    student_id=student.id,
                    date=selected_date
                ).first()
                
                status = attendance.status if attendance else None
                
                if status == 'present':
                    present_count += 1
                elif status == 'absent':
                    absent_count += 1
                
                students_data.append({
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'status': status
                })
            
            groups_data.append({
                'group_name': group.name,
                'students': students_data,
                'total': len(students_data),
                'present': present_count,
                'absent': absent_count
            })
        
        # Excel yaratish
        excel_file = exporter.export_daily_report(
            selected_date,
            groups_data
        )
        
        filename = generate_filename('davomat_hisobot', selected_date)
    
    # Excel faylni yuborish
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route('/reports/data')
@login_required
def reports_data():
    """
    AJAX uchun hisobot ma'lumotlarini JSON formatda qaytarish
    """
    from sqlalchemy import func
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({'error': 'Sanalar ko\'rsatilmagan'}), 400
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Noto\'g\'ri sana formati'}), 400
    
    # Umumiy statistika
    query = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    )
    
    total_records = query.count()
    total_present = query.filter_by(status='present').count()
    total_absent = query.filter_by(status='absent').count()
    
    attendance_percentage = (total_present / total_records * 100) if total_records > 0 else 0
    
    return jsonify({
        'success': True,
        'stats': {
            'total_records': total_records,
            'total_present': total_present,
            'total_absent': total_absent,
            'attendance_percentage': round(attendance_percentage, 1)
        }
    })


@app.route('/reports/student/<int:student_id>')
@login_required
def student_report(student_id):
    """
    Alohida talaba uchun batafsil hisobot
    """
    student = Student.query.get_or_404(student_id)
    
    # Sana oralig'i
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    today = datetime.now().date()
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
    else:
        start_date = today - timedelta(days=30)
        end_date = today
    
    # Statistika
    stats = student.get_attendance_stats(start_date, end_date)
    
    # Batafsil davomat tarixi
    attendance_history = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('student_report.html',
                         student=student,
                         stats=stats,
                         attendance_history=attendance_history,
                         start_date=start_date,
                         end_date=end_date)


# ==========================================
# XAVFSIZLIK VA SESSION BOSHQARUVI
# ==========================================

@app.route('/security/sessions')
@login_required
def security_sessions():
    """
    Aktiv sessionlarni ko'rish va boshqarish
    """
    from models import AdminToken
    from security import get_all_sessions
    from auth import REMEMBER_ME_COOKIE_NAME
    
    # Barcha aktiv sessionlar
    sessions = get_all_sessions()
    
    # Joriy sessionni belgilash
    current_selector = None
    cookie_value = request.cookies.get(REMEMBER_ME_COOKIE_NAME)
    if cookie_value and ':' in cookie_value:
        current_selector = cookie_value.split(':', 1)[0]
    
    # Joriy sessionni belgilash
    for session_info in sessions:
        token = AdminToken.query.get(session_info['id'])
        if token and token.selector == current_selector:
            session_info['is_current'] = True
    
    return render_template('security_sessions.html', sessions=sessions)


@app.route('/security/revoke/<int:session_id>', methods=['POST'])
@login_required
def revoke_session(session_id):
    """
    Muayyan sessionni bekor qilish
    """
    from security import revoke_session as revoke_sess
    
    if revoke_sess(session_id):
        flash('Session bekor qilindi! 🔒', 'success')
    else:
        flash('Session topilmadi! ❌', 'danger')
    
    return redirect(url_for('security_sessions'))


@app.route('/security/revoke-all', methods=['POST'])
@login_required
def revoke_all_sessions():
    """
    Joriy sessiondan tashqari barcha sessionlarni bekor qilish
    """
    from security import revoke_all_sessions_except_current
    from auth import REMEMBER_ME_COOKIE_NAME
    
    # Joriy selector
    current_selector = None
    cookie_value = request.cookies.get(REMEMBER_ME_COOKIE_NAME)
    if cookie_value and ':' in cookie_value:
        current_selector = cookie_value.split(':', 1)[0]
    
    count = revoke_all_sessions_except_current(current_selector)
    
    flash(f'{count} ta session bekor qilindi! 🔒', 'success')
    return redirect(url_for('security_sessions'))


# ==========================================
# ERROR HANDLERS
# ==========================================

# 404 xatosi uchun handler
@app.errorhandler(404)
def not_found_error(error):
    return """
    <!DOCTYPE html>
    <html>
    <head><title>404 - Sahifa topilmadi</title></head>
    <body style="text-align: center; padding: 50px;">
        <h1>📄 404 - Sahifa topilmadi</h1>
        <p>Kechirasiz, siz qidirgan sahifa mavjud emas.</p>
        <a href="/login">Login sahifasiga qaytish</a>
    </body>
    </html>
    """, 404

# 500 xatosi uchun handler
@app.errorhandler(500)
def internal_error(error):
    return """
    <!DOCTYPE html>
    <html>
    <head><title>500 - Server xatosi</title></head>
    <body style="text-align: center; padding: 50px;">
        <h1>⚠️ 500 - Server xatosi</h1>
        <p>Serverda ichki xatolik yuz berdi.</p>
        <a href="/login">Login sahifasiga qaytish</a>
    </body>
    </html>
    """, 500

# ==========================================
# DEVELOPMENT SERVER
# ==========================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
