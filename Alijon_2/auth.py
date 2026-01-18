from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from security import (
    is_device_blocked, record_failed_attempt, clear_failed_attempts,
    is_device_trusted, add_trusted_device
)

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

def init_auth(app):
    """Login manager ni sozlash"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Iltimos, tizimga kiring'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login sahifasi"""
    # Agar allaqachon kirgan bo'lsa
    if current_user.is_authenticated:
        # Ishonchli qurilma ekanligini tekshirish
        if is_device_trusted(current_user.id):
            return redirect(url_for('main.dashboard'))
    
    # Qurilma bloklangan-yo'qligini tekshirish
    if is_device_blocked():
        return render_template('login.html', blocked=True)
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # To'g'ri parol
            clear_failed_attempts()
            login_user(user, remember=remember)
            
            # Qurilmani ishonchli ro'yxatga qo'shish
            add_trusted_device(user.id)
            
            flash('Xush kelibsiz!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            # Noto'g'ri parol
            attempts = record_failed_attempt()
            remaining = 3 - attempts
            
            if remaining > 0:
                flash(f'Noto\'g\'ri login yoki parol! {remaining} ta urinish qoldi.', 'danger')
            else:
                flash('Siz bloklangansiz! Bu qurilmadan tizimga kira olmaysiz.', 'danger')
                return render_template('login.html', blocked=True)
    
    return render_template('login.html', blocked=False)

@auth_bp.route('/logout')
@login_required
def logout():
    """Tizimdan chiqish"""
    logout_user()
    flash('Tizimdan chiqdingiz', 'info')
    return redirect(url_for('auth.login'))
