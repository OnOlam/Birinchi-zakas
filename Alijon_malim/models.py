"""
Database models for Attendance Management System
SQLAlchemy ORM bilan yozilgan
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


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
        """To'liq ism"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """JSON formatga o'tkazish uchun"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
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
