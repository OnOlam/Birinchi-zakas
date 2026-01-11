"""
Security Management Module
Xavfsizlik boshqaruvi - Token management, Rate limiting
"""

from datetime import datetime, timedelta
from collections import defaultdict
import threading


# ==========================================
# RATE LIMITING (Login urinishlarini cheklash)
# ==========================================

class RateLimiter:
    """
    IP address bo'yicha login urinishlarini cheklash
    """
    
    def __init__(self, max_attempts=5, window_minutes=15):
        """
        Args:
            max_attempts: Maksimal urinishlar soni
            window_minutes: Vaqt oynasi (daqiqada)
        """
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, ip_address):
        """
        IP address uchun urinishga ruxsat bormi?
        
        Args:
            ip_address: Client IP address
            
        Returns:
            bool: True agar ruxsat bo'lsa
        """
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=self.window_minutes)
            
            # Eski urinishlarni tozalash
            self.attempts[ip_address] = [
                attempt_time for attempt_time in self.attempts[ip_address]
                if attempt_time > cutoff
            ]
            
            # Urinishlar sonini tekshirish
            if len(self.attempts[ip_address]) >= self.max_attempts:
                return False
            
            return True
    
    def record_attempt(self, ip_address):
        """
        Login urinishini yozib olish
        
        Args:
            ip_address: Client IP address
        """
        with self.lock:
            self.attempts[ip_address].append(datetime.now())
    
    def reset(self, ip_address):
        """
        IP address uchun urinishlarni tozalash (muvaffaqiyatli login)
        
        Args:
            ip_address: Client IP address
        """
        with self.lock:
            if ip_address in self.attempts:
                del self.attempts[ip_address]
    
    def cleanup(self):
        """
        Barcha eski urinishlarni tozalash
        """
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(minutes=self.window_minutes)
            
            for ip_address in list(self.attempts.keys()):
                self.attempts[ip_address] = [
                    attempt_time for attempt_time in self.attempts[ip_address]
                    if attempt_time > cutoff
                ]
                
                # Agar bo'sh bo'lsa, o'chirish
                if not self.attempts[ip_address]:
                    del self.attempts[ip_address]


# Global rate limiter
rate_limiter = RateLimiter(max_attempts=5, window_minutes=15)


# ==========================================
# TOKEN MANAGEMENT HELPER FUNCTIONS
# ==========================================

def get_active_sessions():
    """
    Aktiv tokenlar sonini olish
    
    Returns:
        int: Aktiv tokenlar soni
    """
    from models import AdminToken
    
    now = datetime.utcnow()
    active_count = AdminToken.query.filter(
        AdminToken.expires_at > now
    ).count()
    
    return active_count


def get_all_sessions():
    """
    Barcha aktiv sessionlar haqida ma'lumot
    
    Returns:
        list: Session ma'lumotlari
    """
    from models import AdminToken
    
    now = datetime.utcnow()
    sessions = AdminToken.query.filter(
        AdminToken.expires_at > now
    ).order_by(AdminToken.created_at.desc()).all()
    
    session_list = []
    for session in sessions:
        session_list.append({
            'id': session.id,
            'created_at': session.created_at,
            'expires_at': session.expires_at,
            'last_used': session.last_used,
            'user_agent': session.user_agent[:50] + '...' if len(session.user_agent) > 50 else session.user_agent,
            'ip_address': session.ip_address,
            'is_current': False  # Bu qismni app.py'da belgilash kerak
        })
    
    return session_list


def revoke_session(session_id):
    """
    Muayyan sessionni bekor qilish
    
    Args:
        session_id: Token ID
        
    Returns:
        bool: True agar muvaffaqiyatli bo'lsa
    """
    from models import AdminToken, db
    
    token = AdminToken.query.get(session_id)
    if token:
        db.session.delete(token)
        db.session.commit()
        return True
    
    return False


def revoke_all_sessions_except_current(current_selector=None):
    """
    Joriy sessiondan tashqari barcha sessionlarni bekor qilish
    
    Args:
        current_selector: Joriy token selector (saqlanadi)
        
    Returns:
        int: Bekor qilingan sessionlar soni
    """
    from models import AdminToken, db
    
    if current_selector:
        # Joriy tokendan tashqari hammasini o'chirish
        tokens = AdminToken.query.filter(
            AdminToken.selector != current_selector
        ).all()
    else:
        # Barcha tokenlarni o'chirish
        tokens = AdminToken.query.all()
    
    count = len(tokens)
    
    for token in tokens:
        db.session.delete(token)
    
    db.session.commit()
    
    return count


# ==========================================
# SECURITY AUDIT LOG (ixtiyoriy)
# ==========================================

class SecurityAuditLog:
    """
    Xavfsizlik hodisalarini logga yozish
    Production'da database yoki file'ga yozilishi kerak
    """
    
    @staticmethod
    def log_login_success(username, ip_address, user_agent, method='password'):
        """
        Muvaffaqiyatli login
        """
        print(f"[LOGIN SUCCESS] {username} from {ip_address} via {method}")
        # Bu yerda database'ga yoki file'ga yoziladi
    
    @staticmethod
    def log_login_failure(username, ip_address, reason='Invalid credentials'):
        """
        Muvaffaqiyatsiz login urinishi
        """
        print(f"[LOGIN FAILED] {username} from {ip_address} - {reason}")
        # Bu yerda database'ga yoki file'ga yoziladi
    
    @staticmethod
    def log_logout(username, ip_address):
        """
        Logout
        """
        print(f"[LOGOUT] {username} from {ip_address}")
    
    @staticmethod
    def log_token_created(ip_address, user_agent):
        """
        Remember me token yaratildi
        """
        print(f"[TOKEN CREATED] for {ip_address}")
    
    @staticmethod
    def log_token_revoked(selector, reason='Manual logout'):
        """
        Token bekor qilindi
        """
        print(f"[TOKEN REVOKED] {selector} - {reason}")
    
    @staticmethod
    def log_suspicious_activity(ip_address, reason):
        """
        Shubhali faoliyat
        """
        print(f"[SUSPICIOUS] {ip_address} - {reason}")


# ==========================================
# SECURITY UTILITIES
# ==========================================

def is_secure_connection():
    """
    HTTPS orqali ulanganmi?
    
    Returns:
        bool: True agar HTTPS bo'lsa
    """
    from flask import request
    
    return request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'


def get_real_ip():
    """
    Client'ning haqiqiy IP addressini olish
    Proxy va load balancer hisobga olinadi
    
    Returns:
        str: IP address
    """
    from flask import request
    
    # X-Forwarded-For header'dan (proxy orqali)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # X-Real-IP header'dan
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    
    # To'g'ridan-to'g'ri ulanish
    return request.remote_addr or '0.0.0.0'


def validate_session_security(token_obj, request_ip=None, request_ua=None):
    """
    Session xavfsizligini tekshirish
    IP yoki User-Agent o'zgargan bo'lsa, shubhali hisoblanadi
    
    Args:
        token_obj: AdminToken object
        request_ip: Joriy request IP
        request_ua: Joriy request User-Agent
        
    Returns:
        bool: True agar xavfsiz bo'lsa
    """
    # IP address o'zgargan bo'lsa (ixtiyoriy - juda qattiq)
    # if token_obj.ip_address and request_ip:
    #     if token_obj.ip_address != request_ip:
    #         SecurityAuditLog.log_suspicious_activity(
    #             request_ip, 
    #             f"IP mismatch: expected {token_obj.ip_address}"
    #         )
    #         return False
    
    # User-Agent o'zgargan bo'lsa (recommended)
    if token_obj.user_agent and request_ua:
        if token_obj.user_agent != request_ua:
            SecurityAuditLog.log_suspicious_activity(
                request_ip or 'unknown', 
                "User-Agent mismatch"
            )
            # Bu yerda False qaytarish yoki warning berish mumkin
            # return False
    
    return True


# ==========================================
# INITIALIZATION
# ==========================================

def init_security(app):
    """
    Security module'ni ishga tushirish
    
    Args:
        app: Flask application
    """
    # Rate limiter cleanup (har 1 soatda)
    @app.before_request
    def cleanup_rate_limiter():
        # Har 100-requestda tozalash (taxminiy)
        import random
        if random.randint(1, 100) == 1:
            rate_limiter.cleanup()
    
    print("✅ Security module ishga tushdi")


if __name__ == '__main__':
    # Test
    print("=== SECURITY MODULE TEST ===")
    
    # Rate limiter test
    limiter = RateLimiter(max_attempts=3, window_minutes=1)
    
    test_ip = '192.168.1.1'
    
    for i in range(5):
        allowed = limiter.is_allowed(test_ip)
        print(f"Attempt {i+1}: {'Allowed' if allowed else 'Blocked'}")
        if allowed:
            limiter.record_attempt(test_ip)
