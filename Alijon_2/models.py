from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Admin foydalanuvchi"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Group(db.Model):
    """Guruhlar"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    
    students = db.relationship('Student', backref='group', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='group', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Group {self.name}>'

class Student(db.Model):
    """Talabalar"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"
    
    def __repr__(self):
        return f'<Student {self.full_name}>'

class Attendance(db.Model):
    """Davomat yozuvlari - har bir talaba uchun har bir kun"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # 7 ta soat uchun ustunlar (True = keldi, False = kelmadi, None = belgilanmagan)
    hour_1 = db.Column(db.Boolean, default=None)
    hour_2 = db.Column(db.Boolean, default=None)
    hour_3 = db.Column(db.Boolean, default=None)
    hour_4 = db.Column(db.Boolean, default=None)
    hour_5 = db.Column(db.Boolean, default=None)
    hour_6 = db.Column(db.Boolean, default=None)
    hour_7 = db.Column(db.Boolean, default=None)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='unique_student_date'),
    )
    
    def get_hours_list(self):
        """7 ta soatning holatini ro'yxat sifatida qaytaradi"""
        return [
            self.hour_1, self.hour_2, self.hour_3, self.hour_4,
            self.hour_5, self.hour_6, self.hour_7
        ]
    
    def set_hours_list(self, hours_list):
        """Ro'yxatdan 7 ta soatni o'rnatadi"""
        if len(hours_list) == 7:
            self.hour_1, self.hour_2, self.hour_3, self.hour_4, \
            self.hour_5, self.hour_6, self.hour_7 = hours_list
    
    def count_present(self):
        """Nechta soat kelganini hisoblaydi"""
        return sum(1 for h in self.get_hours_list() if h is True)
    
    def count_absent(self):
        """Nechta soat kelmaganini hisoblaydi"""
        return sum(1 for h in self.get_hours_list() if h is False)
    
    def __repr__(self):
        return f'<Attendance {self.student.full_name} - {self.date}>'

class BlockedDevice(db.Model):
    """Bloklangan qurilmalar"""
    __tablename__ = 'blocked_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(500), nullable=False)
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    failed_attempts = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('ip_address', 'user_agent', name='unique_device'),
    )

class TrustedDevice(db.Model):
    """Ishonchli qurilmalar (max 3 ta)"""
    __tablename__ = 'trusted_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(500), nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='trusted_devices')
