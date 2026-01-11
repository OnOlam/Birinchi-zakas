"""
Database models for Attendance Management System
SQLAlchemy ORM bilan yozilgan + Secure Token System
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import hashlib

db = SQLAlchemy()


class AdminToken(db.Model):
    """
    Admin "Remember Me" tokenlarini saqlash
    Xavfsiz authentication uchun
    """
    __tablename__ = 'admin_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(256), unique=True, nullable=False, index=True)
    selector = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminToken {self.selector}>'
    
    @staticmethod
    def generate_token(user_agent=None, ip_address=None, remember_days=30):
        """
        Yangi "Remember Me" token yaratish
        
        Returns:
            tuple: (selector, validator, token_object)
        """
        # Selector: Tokenni topish uchun
        selector = secrets.token_urlsafe(32)
        
        # Validator: Tasdiqlash uchun (faqat bir marta ko'rsatiladi)
        validator = secrets.token_urlsafe(32)
        
        # Validator'ni hash qilish (database'da saqlash uchun)
        token_hash = hashlib.sha256(validator.encode()).hexdigest()
        
        # Expires date
        expires_at = datetime.utcnow() + timedelta(days=remember_days)
        
        # Token object yaratish
        token = AdminToken(
            token_hash=token_hash,
            selector=selector,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at
        )
        
        db.session.add(token)
        db.session.commit()
        
        return selector, validator, token
    
    @staticmethod
    def verify_token(selector, validator):
        """
        Tokenni tekshirish
        
        Args:
            selector: Token selector
            validator: Token validator
            
        Returns:
            bool: True agar token to'g'ri va amal qilsa
        """
        token = AdminToken.query.filter_by(selector=selector).first()
        
        if not token:
            return False
        
        # Muddati tugaganmi tekshirish
        if token.expires_at < datetime.utcnow():
            db.session.delete(token)
            db.session.commit()
            return False
        
        # Hash'ni tekshirish
        validator_hash = hashlib.sha256(validator.encode()).hexdigest()
        
        if token.token_hash == validator_hash:
            # Last used yangilash
            token.last_used = datetime.utcnow()
            db.session.commit()
            return True
        
        # Agar hash mos kelmasa, token o'chiriladi (xavfsizlik)
        db.session.delete(token)
        db.session.commit()
        return False
    
    @staticmethod
    def revoke_token(selector):
        """
        Tokenni bekor qilish (logout)
        """
        token = AdminToken.query.filter_by(selector=selector).first()
        if token:
            db.session.delete(token)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def cleanup_expired():
        """
        Muddati tugagan tokenlarni tozalash
        """
        expired = AdminToken.query.filter(
            AdminToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired:
            db.session.delete(token)
        
        db.session.commit()
        return len(expired)
    
    @staticmethod
    def revoke_all():
        """
        Barcha tokenlarni bekor qilish (xavfsizlik)
        """
        count = AdminToken.query.count()
        AdminToken.query.delete()
        db.session.commit()
        return count


class Group(db.Model):
    """
    Guruh modeli
    Talabalar guruhlarga biriktiriladi
    """
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relationship: Bir guruhda ko'p talaba bo'lishi mumkin
    students = db.relationship('Student', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """JSON formatga o'tkazish uchun"""
        return {
            'id': self.id,
            'name': self.name,
            'students_count': len([s for s in self.students if s.active])
        }


class Student(db.Model):
    """
    Talaba modeli
    Har bir talaba bitta guruhga tegishli
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))  # Otchestvo (sharif)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship: Talabaning ko'p davomatlari bo'lishi mumkin
    attendances = db.relationship('Attendance', backref='student', lazy=True, 
                                  cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """To'liq ism (ism + familiya)"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name_with_middle(self):
        """To'liq ism sharif bilan (ism + otchestvo + familiya)"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return self.full_name
    
    def to_dict(self):
        """JSON formatga o'tkazish uchun"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'middle_name': self.middle_name,
            'full_name': self.full_name,
            'full_name_with_middle': self.full_name_with_middle,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'active': self.active
        }
    
    def get_attendance_stats(self, start_date=None, end_date=None):
        """
        Talabaning statistikasini olish
        """
        query = Attendance.query.filter_by(student_id=self.id)
        
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)
        
        total = query.count()
        present = query.filter_by(status='present').count()
        absent = query.filter_by(status='absent').count()
        
        percentage = (present / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': round(percentage, 2)
        }


class Attendance(db.Model):
    """
    Davomat modeli
    Har bir talabaning kunlik davomati saqlanadi
    """
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), nullable=False)  # 'present' yoki 'absent'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # MUHIM: Bir talaba bir kunda faqat BIR marta yozilishi uchun
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='unique_student_date'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date} - {self.status}>'
    
    def to_dict(self):
        """JSON formatga o'tkazish uchun"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'date': self.date.strftime('%Y-%m-%d'),
            'status': self.status,
            'status_uz': 'Keldi' if self.status == 'present' else 'Kelmadi'
        }
    
    @staticmethod
    def get_by_date(date, group_id=None):
        """
        Muayyan sanada davomatni olish
        Faqat ACTIVE talabalar ko'rinadi
        """
        query = db.session.query(Attendance).join(Student).filter(
            Attendance.date == date,
            Student.active == True
        )
        
        if group_id:
            query = query.filter(Student.group_id == group_id)
        
        return query.all()
    
    @staticmethod
    def mark_attendance(student_id, date, status):
        """
        Davomatni belgilash yoki yangilash
        Agar avvaldan mavjud bo'lsa - yangilaydi
        Aks holda - yangi qo'shadi
        """
        existing = Attendance.query.filter_by(
            student_id=student_id,
            date=date
        ).first()
        
        if existing:
            # Mavjud davomatni yangilash
            existing.status = status
            return existing
        else:
            # Yangi davomat qo'shish
            new_attendance = Attendance(
                student_id=student_id,
                date=date,
                status=status
            )
            db.session.add(new_attendance)
            return new_attendance


# Helper funksiyalar

def init_db(app):
    """
    Database'ni ishga tushirish
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Database yaratildi!")


def seed_data():
    """
    Test ma'lumotlar qo'shish (ixtiyoriy)
    """
    # Agar guruh bo'lmasa test guruh qo'shish
    if Group.query.count() == 0:
        test_group = Group(name="Python 101")
        db.session.add(test_group)
        db.session.commit()
        print("✅ Test guruh qo'shildi")
        
        # Test talabalar
        students = [
            Student(first_name="Ali", last_name="Valiyev", group_id=test_group.id),
            Student(first_name="Laylo", last_name="Karimova", group_id=test_group.id),
            Student(first_name="Bobur", last_name="Toshmatov", group_id=test_group.id),
        ]
        db.session.add_all(students)
        db.session.commit()
        print("✅ Test talabalar qo'shildi")
