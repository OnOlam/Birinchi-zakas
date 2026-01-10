"""
Login va Authentication tizimi
Oddiy va xavfsiz - faqat 1 admin uchun
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import check_password_hash, generate_password_hash


# ==========================================
# ADMIN MA'LUMOTLARI (oldindan belgilangan)
# ==========================================

ADMIN_CREDENTIALS = {
    'username': 'admin',
    # Parol: admin123 (hash qilingan)
    'password_hash': generate_password_hash('admin123')
}

# Production uchun environment variable ishlatish kerak:
# import os
# ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
# ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')


# ==========================================
# LOGIN TEKSHIRISH FUNKSIYALARI
# ==========================================

def check_login(username, password):
    """
    Username va parolni tekshirish
    
    Args:
        username: Foydalanuvchi nomi
        password: Parol (oddiy text)
    
    Returns:
        True - agar to'g'ri bo'lsa
        False - agar noto'g'ri bo'lsa
    """
    if username == ADMIN_CREDENTIALS['username']:
        return check_password_hash(ADMIN_CREDENTIALS['password_hash'], password)
    return False


def is_logged_in():
    """
    Foydalanuvchi login qilganmi yoki yo'qmi tekshirish
    
    Returns:
        True - agar session mavjud bo'lsa
        False - agar session bo'lmasa
    """
    return 'logged_in' in session and session['logged_in'] is True


def get_current_user():
    """
    Hozirgi foydalanuvchi ma'lumotlarini olish
    
    Returns:
        dict: username va boshqa ma'lumotlar
        None: agar login qilmagan bo'lsa
    """
    if is_logged_in():
        return {
            'username': session.get('username'),
            'login_time': session.get('login_time')
        }
    return None


# ==========================================
# SESSION BOSHQARUVI
# ==========================================

def login_user(username):
    """
    Foydalanuvchini session'ga qo'shish (login qilish)
    
    Args:
        username: Foydalanuvchi nomi
    """
    from datetime import datetime
    
    session['logged_in'] = True
    session['username'] = username
    session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    session.permanent = True  # Session esda qolsin


def logout_user():
    """
    Foydalanuvchini session'dan o'chirish (logout qilish)
    """
    session.clear()


# ==========================================
# DECORATOR - SAHIFALARNI HIMOYALASH
# ==========================================

def login_required(f):
    """
    Decorator: Login talab qilinadigan sahifalar uchun
    
    Foydalanish:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            return "Bu himoyalangan sahifa"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Iltimos avval login qiling!', 'warning')
            # Qaytish uchun URL'ni saqlash
            session['next_url'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# PAROLNI O'ZGARTIRISH (ixtiyoriy)
# ==========================================

def change_password(old_password, new_password):
    """
    Admin parolini o'zgartirish
    
    DIQQAT: Bu funksiya faqat demonstratsiya uchun.
    Production'da parol database'da saqlanishi kerak!
    
    Args:
        old_password: Eski parol
        new_password: Yangi parol
    
    Returns:
        True - agar muvaffaqiyatli bo'lsa
        False - agar eski parol noto'g'ri bo'lsa
    """
    if check_password_hash(ADMIN_CREDENTIALS['password_hash'], old_password):
        ADMIN_CREDENTIALS['password_hash'] = generate_password_hash(new_password)
        return True
    return False


# ==========================================
# FLASK ROUTES (app.py da ishlatish uchun)
# ==========================================

"""
Quyidagi kodlarni app.py faylingizga qo'shing:

from flask import Flask, render_template, request, redirect, url_for, flash
from auth import (
    check_login, login_user, logout_user, 
    login_required, is_logged_in
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Agar allaqachon login qilgan bo'lsa
    if is_logged_in():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Login tekshirish
        if check_login(username, password):
            login_user(username)
            flash('Xush kelibsiz!', 'success')
            
            # Agar oldingi sahifa bo'lsa - u yerga qaytish
            next_url = session.pop('next_url', None)
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Username yoki parol noto\'g\'ri!', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Tizimdan chiqdingiz', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
"""


# ==========================================
# YORDAMCHI FUNKSIYALAR
# ==========================================

def init_auth(app):
    """
    Flask app uchun authentication sozlamalari
    
    Args:
        app: Flask application
    """
    from datetime import timedelta
    
    # Session konfiguratsiyasi
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    print("✅ Authentication tizimi ishga tushdi")


# ==========================================
# PAROLNI HASH QILISH (yangi parol uchun)
# ==========================================

def generate_new_password_hash(password):
    """
    Yangi parol uchun hash yaratish
    Terminal'da ishlatish:
    
    >>> from auth import generate_new_password_hash
    >>> generate_new_password_hash('yangi_parol')
    
    Args:
        password: Oddiy text parol
    
    Returns:
        str: Hash qilingan parol
    """
    return generate_password_hash(password)


if __name__ == '__main__':
    # Test qilish
    print("=== AUTH MODULE TEST ===")
    print(f"Admin username: {ADMIN_CREDENTIALS['username']}")
    print(f"Test parol: admin123")
    print(f"Login test: {check_login('admin', 'admin123')}")
    print(f"Noto'g'ri parol: {check_login('admin', 'wrong')}")
