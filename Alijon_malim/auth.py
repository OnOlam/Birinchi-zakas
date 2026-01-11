"""
Secure Authentication System with "Remember Me" Token
Xavfsiz login tizimi - Token-based authentication
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import secrets
import hashlib
import os  # os modulini import qilish


# ==========================================
# ADMIN MA'LUMOTLARI
# ==========================================

# Production uchun environment variable ishlatish kerak:
#ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
#ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv('ADMIN_PASSWORD', '928100796'))

# Yoki oddiy test versiyasi (faqat development uchun):
# ADMIN_CREDENTIALS = {
#     'username': 'admin',
#     'password_hash': generate_password_hash('928100796')
# }

ADMIN_CREDENTIALS = {
    'username': 'admin',  # ← LOGIN
    'password_hash': generate_password_hash('928100796')  # ← PAROL
}


# ==========================================
# COOKIE SOZLAMALARI
# ==========================================

REMEMBER_ME_COOKIE_NAME = 'remember_token'
REMEMBER_ME_DURATION_DAYS = 30  # Token 30 kun amal qiladi


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
            'login_time': session.get('login_time'),
            'login_method': session.get('login_method', 'password')
        }
    return None


# ==========================================
# SESSION BOSHQARUVI
# ==========================================

def login_user(username, login_method='password'):
    """
    Foydalanuvchini session'ga qo'shish (login qilish)
    
    Args:
        username: Foydalanuvchi nomi
        login_method: 'password' yoki 'token'
    """
    session['logged_in'] = True
    session['username'] = username
    session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    session['login_method'] = login_method
    session.permanent = True  # Session esda qolsin


def logout_user():
    """
    Foydalanuvchini session'dan o'chirish (logout qilish)
    """
    session.clear()


# ==========================================
# REMEMBER ME TOKEN BOSHQARUVI
# ==========================================

def create_remember_me_token(response, user_agent=None, ip_address=None):
    """
    "Remember Me" token yaratish va cookie'ga qo'shish
    
    Args:
        response: Flask response object
        user_agent: User agent string
        ip_address: IP address
        
    Returns:
        Modified response with cookie
    """
    from models import AdminToken
    
    # Token yaratish
    selector, validator, token_obj = AdminToken.generate_token(
        user_agent=user_agent,
        ip_address=ip_address,
        remember_days=REMEMBER_ME_DURATION_DAYS
    )
    
    # Cookie value: selector:validator formatida
    cookie_value = f"{selector}:{validator}"
    
    # Cookie sozlamalari
    expires = datetime.utcnow() + timedelta(days=REMEMBER_ME_DURATION_DAYS)
    
    # Cookie qo'shish
    response.set_cookie(
        REMEMBER_ME_COOKIE_NAME,
        value=cookie_value,
        max_age=REMEMBER_ME_DURATION_DAYS * 24 * 60 * 60,
        expires=expires,
        httponly=True,      # JavaScript orqali o'qib bo'lmaydi
        secure=False,       # Production'da True bo'lishi kerak (HTTPS)
        samesite='Lax'      # CSRF himoyasi
    )
    
    return response


def verify_remember_me_token():
    """
    Cookie'dagi "Remember Me" tokenni tekshirish
    
    Returns:
        bool: True agar token to'g'ri bo'lsa
    """
    from models import AdminToken
    
    # Cookie'dan tokenni olish
    cookie_value = request.cookies.get(REMEMBER_ME_COOKIE_NAME)
    
    if not cookie_value:
        return False
    
    # Tokenni ajratish
    try:
        selector, validator = cookie_value.split(':', 1)
    except ValueError:
        return False
    
    # Tokenni tekshirish
    return AdminToken.verify_token(selector, validator)


def revoke_remember_me_token(response):
    """
    "Remember Me" tokenni bekor qilish va cookie'ni o'chirish
    
    Args:
        response: Flask response object
        
    Returns:
        Modified response without cookie
    """
    from models import AdminToken
    
    # Cookie'dan tokenni olish
    cookie_value = request.cookies.get(REMEMBER_ME_COOKIE_NAME)
    
    if cookie_value:
        try:
            selector, _ = cookie_value.split(':', 1)
            # Database'dan tokenni o'chirish
            AdminToken.revoke_token(selector)
        except ValueError:
            pass
    
    # Cookie'ni o'chirish
    response.delete_cookie(REMEMBER_ME_COOKIE_NAME)
    
    return response


def cleanup_old_tokens():
    """
    Muddati tugagan tokenlarni tozalash
    Cron job yoki background task sifatida ishlatiladi
    """
    from models import AdminToken
    
    return AdminToken.cleanup_expired()


# ==========================================
# AUTO-LOGIN TEKSHIRISH
# ==========================================

def try_auto_login():
    """
    Cookie orqali avtomatik login qilishga urinish
    
    Returns:
        bool: True agar muvaffaqiyatli bo'lsa
    """
    # Agar allaqachon login qilgan bo'lsa
    if is_logged_in():
        return True
    
    # Remember me token tekshirish
    if verify_remember_me_token():
        # Auto-login
        login_user(ADMIN_CREDENTIALS['username'], login_method='token')
        flash('Avtomatik login qilindi! 🔐', 'info')
        return True
    
    return False


# ==========================================
# DECORATOR - SAHIFALARNI HIMOYALASH
# ==========================================

def login_required(f):
    """
    Decorator: Login talab qilinadigan sahifalar uchun
    Auto-login'ni ham tekshiradi
    
    Foydalanish:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            return "Bu himoyalangan sahifa"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Avval auto-login'ni tekshirish
        if not is_logged_in():
            if not try_auto_login():
                flash('Iltimos avval login qiling!', 'warning')
                # Qaytish uchun URL'ni saqlash
                session['next_url'] = request.url
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# XAVFSIZLIK FUNKSIYALARI
# ==========================================

def get_client_info():
    """
    Client ma'lumotlarini olish (User-Agent va IP)
    
    Returns:
        tuple: (user_agent, ip_address)
    """
    user_agent = request.headers.get('User-Agent', '')[:500]  # Max 500 char
    
    # IP address (proxy orqali bo'lsa ham)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address:
        ip_address = ip_address.split(',')[0].strip()
    
    return user_agent, ip_address


def is_suspicious_login():
    """
    Shubhali login urinishini aniqlash
    
    Returns:
        bool: True agar shubhali bo'lsa
    """
    # Bu yerda qo'shimcha xavfsizlik tekshiruvlari qo'shish mumkin:
    # - Bir IP'dan ko'p urinishlar
    # - Turli User-Agent'lar
    # - Rate limiting
    # - Geo-location tekshiruvi
    
    return False


def rate_limit_check():
    """
    Login urinishlarini cheklash (Rate limiting)
    
    Returns:
        bool: True agar ruxsat etilsa
    """
    # Bu yerda rate limiting logikasi qo'shiladi
    # Misol: Bir IP'dan 5 ta login urinishi 15 daqiqada
    
    return True


# ==========================================
# PAROLNI O'ZGARTIRISH
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
        bool: True - agar muvaffaqiyatli bo'lsa
    """
    if check_password_hash(ADMIN_CREDENTIALS['password_hash'], old_password):
        ADMIN_CREDENTIALS['password_hash'] = generate_password_hash(new_password)
        
        # Barcha tokenlarni bekor qilish (xavfsizlik)
        from models import AdminToken
        AdminToken.revoke_all()
        
        return True
    return False


# ==========================================
# FLASK SOZLAMALARI
# ==========================================

def init_auth(app):
    """
    Flask app uchun authentication sozlamalari
    
    Args:
        app: Flask application
    """
    # Session konfiguratsiyasi
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Token cleanup (har safar app ishga tushganda)
    with app.app_context():
        cleanup_old_tokens()
    
    print("✅ Authentication tizimi ishga tushdi")


# ==========================================
# HELPER FUNKSIYALAR
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
    print("=== SECURE AUTH MODULE TEST ===")
    print(f"Admin username: {ADMIN_CREDENTIALS['username']}")
    print(f"Test parol: admin123")
    print(f"Login test: {check_login('admin', 'admin123')}")
    print(f"Noto'g'ri parol: {check_login('admin', 'wrong')}")
    print(f"Remember me duration: {REMEMBER_ME_DURATION_DAYS} days")
