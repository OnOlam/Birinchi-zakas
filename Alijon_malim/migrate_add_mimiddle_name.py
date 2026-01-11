"""
Database Migration Script
Student modeliga middle_name (otchestvo) ustunini qo'shish

ISHLATISH:
python migrate_add_middle_name.py
"""

from app import app, db
from models import Student


def add_middle_name_column():
    """
    Student jadvaliga middle_name ustunini qo'shish
    """
    with app.app_context():
        try:
            # SQLite uchun ALTER TABLE qo'llab-quvvatlanadi
            with db.engine.connect() as conn:
                # Ustun mavjudligini tekshirish
                result = conn.execute(db.text("PRAGMA table_info(students)"))
                columns = [row[1] for row in result]
                
                if 'middle_name' not in columns:
                    print("📝 middle_name ustuni qo'shilmoqda...")
                    
                    # Ustun qo'shish
                    conn.execute(db.text(
                        "ALTER TABLE students ADD COLUMN middle_name VARCHAR(100)"
                    ))
                    conn.commit()
                    
                    print("✅ middle_name ustuni muvaffaqiyatli qo'shildi!")
                    print("✅ Endi talabalar otchestvo bilan saqlanadi")
                else:
                    print("ℹ️  middle_name ustuni allaqachon mavjud")
        
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            print("\n📌 Agar database mavjud bo'lmasa:")
            print("   1. python app.py ni ishga tushiring")
            print("   2. Database avtomatik yaratiladi")
            print("   3. Keyin bu skriptni qayta ishga tushiring")


def test_migration():
    """
    Migration'ni test qilish
    """
    with app.app_context():
        try:
            # Birinchi talabani olish
            student = Student.query.first()
            
            if student:
                print(f"\n📊 Test talaba:")
                print(f"   Ism: {student.first_name}")
                print(f"   Otchestvo: {student.middle_name or '(kiritilmagan)'}")
                print(f"   Familiya: {student.last_name}")
                print(f"   To'liq: {student.full_name_with_middle}")
            else:
                print("\nℹ️  Database'da talabalar yo'q")
        
        except Exception as e:
            print(f"❌ Test xatolik: {e}")


if __name__ == '__main__':
    print("=" * 50)
    print("DATABASE MIGRATION")
    print("Student jadvaliga 'middle_name' qo'shish")
    print("=" * 50)
    print()
    
    # Migration
    add_middle_name_column()
    
    # Test
    print()
    test_migration()
    
    print()
    print("=" * 50)
    print("✅ Migration tugadi!")
    print("=" * 50)
