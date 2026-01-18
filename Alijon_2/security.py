from flask import request
from models import db, BlockedDevice, TrustedDevice
from datetime import datetime

def get_device_fingerprint():
    """Qurilma identifikatorini olish"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    return ip, user_agent

def is_device_blocked():
    """Qurilma bloklangan yoki yo'qligini tekshirish"""
    ip, user_agent = get_device_fingerprint()
    blocked = BlockedDevice.query.filter_by(
        ip_address=ip,
        user_agent=user_agent
    ).first()
    return blocked is not None

def block_device():
    """Qurilmani bloklash"""
    ip, user_agent = get_device_fingerprint()
    
    blocked = BlockedDevice.query.filter_by(
        ip_address=ip,
        user_agent=user_agent
    ).first()
    
    if not blocked:
        blocked = BlockedDevice(
            ip_address=ip,
            user_agent=user_agent,
            failed_attempts=1
        )
        db.session.add(blocked)
    else:
        blocked.failed_attempts += 1
    
    db.session.commit()

def record_failed_attempt():
    """Noto'g'ri urinishni yozish"""
    ip, user_agent = get_device_fingerprint()
    
    blocked = BlockedDevice.query.filter_by(
        ip_address=ip,
        user_agent=user_agent
    ).first()
    
    if not blocked:
        blocked = BlockedDevice(
            ip_address=ip,
            user_agent=user_agent,
            failed_attempts=1
        )
        db.session.add(blocked)
    else:
        blocked.failed_attempts += 1
        
        # 3 ta noto'g'ri urinish = blok
        if blocked.failed_attempts >= 3:
            blocked.blocked_at = datetime.utcnow()
    
    db.session.commit()
    return blocked.failed_attempts

def clear_failed_attempts():
    """Muvaffaqiyatli kirishdan keyin urinishlarni tozalash"""
    ip, user_agent = get_device_fingerprint()
    
    blocked = BlockedDevice.query.filter_by(
        ip_address=ip,
        user_agent=user_agent
    ).first()
    
    if blocked:
        db.session.delete(blocked)
        db.session.commit()

def is_device_trusted(user_id):
    """Qurilma ishonchli ro'yxatda ekanligini tekshirish"""
    ip, user_agent = get_device_fingerprint()
    
    trusted = TrustedDevice.query.filter_by(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent
    ).first()
    
    if trusted:
        # Oxirgi kirish vaqtini yangilash
        trusted.last_login = datetime.utcnow()
        db.session.commit()
        return True
    
    return False

def add_trusted_device(user_id):
    """Qurilmani ishonchli ro'yxatga qo'shish (max 3 ta)"""
    ip, user_agent = get_device_fingerprint()
    
    # Allaqachon bor-yo'qligini tekshirish
    existing = TrustedDevice.query.filter_by(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent
    ).first()
    
    if existing:
        existing.last_login = datetime.utcnow()
        db.session.commit()
        return True
    
    # Qancha qurilma mavjudligini tekshirish
    count = TrustedDevice.query.filter_by(user_id=user_id).count()
    
    if count >= 3:
        # Eng eski qurilmani o'chirish
        oldest = TrustedDevice.query.filter_by(user_id=user_id).order_by(
            TrustedDevice.last_login.asc()
        ).first()
        db.session.delete(oldest)
    
    # Yangi qurilmani qo'shish
    new_device = TrustedDevice(
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent
    )
    db.session.add(new_device)
    db.session.commit()
    return True
