# 📚 Davomat Tizimi - Attendance Management System

Talabalar davomatini boshqarish uchun zamonaviy va qulay web ilova.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 Loyiha Haqida

**Davomat Tizimi** - bu o'qituvchilar uchun mo'ljallangan oddiy va samarali veb-ilova bo'lib, talabalarning kunlik davomatini boshqarish, hisobotlarni ko'rish va statistikani tahlil qilish imkonini beradi.

### ✨ Asosiy Xususiyatlar

- ✅ **Davomat belgilash** - Kunlik davomat qo'yish (mobil uchun optimallashtirilgan)
- 👥 **Talabalar boshqaruvi** - Talabalarni qo'shish, o'chirish va tahrirlash
- 📁 **Guruhlar** - Talabalarni guruhlarga ajratish
- 📊 **Hisobotlar** - Kunlik, haftalik va oylik statistika
- 📱 **Responsive dizayn** - Telefon, planshet va kompyuter uchun
- 🔐 **Xavfsiz login** - Admin uchun authentication

---

## 🖼️ Screenshot'lar

### Dashboard
Umumiy statistika va tezkor harakatlar

### Davomat Belgilash
Qulay va tez davomat qo'yish interfeysi

### Hisobotlar
Batafsil statistika va tahlil

---

## 🛠️ Texnologiyalar

### Backend
- **Python 3.11** - Dasturlash tili
- **Flask 3.0** - Web framework
- **SQLAlchemy** - ORM (Object-Relational Mapping)
- **SQLite** - Database

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling (responsive, mobile-first)
- **JavaScript (Vanilla)** - Interaktivlik

### Production
- **Gunicorn** - WSGI HTTP Server
- **Render.com / Railway.app** - Hosting

---

## 📋 Talablar

- Python 3.11 yoki yuqori
- pip (Python package manager)
- Git

---

## 🚀 O'rnatish (Development)

### 1. Repository'ni clone qiling

```bash
git clone https://github.com/username/attendance-system.git
cd attendance-system
```

### 2. Virtual environment yaratish

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. Environment variables sozlash

```bash
cp .env.example .env
```

`.env` faylini tahrirlang:
```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 5. Database yaratish

```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 6. Serverni ishga tushirish

```bash
python app.py
```

Brauzerda oching: `http://localhost:5000`

---

## 🔐 Login Ma'lumotlari

**Default admin:**
- Username: `admin`
- Parol: `admin123`

> ⚠️ **Muhim:** Production'da parolni o'zgartiring!

---

## 📂 Loyiha Strukturasi

```
attendance-system/
├── app.py                 # Asosiy Flask application
├── models.py              # Database models (Group, Student, Attendance)
├── auth.py                # Authentication logic
├── config.py              # Configuration (dev/prod)
├── requirements.txt       # Python dependencies
├── Procfile              # Production server command
├── runtime.txt           # Python version
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
│
├── templates/            # HTML templates
│   ├── login.html        # Login page
│   ├── dashboard.html    # Main dashboard
│   ├── admin_panel.html  # Admin management
│   ├── attendance.html   # Mark attendance
│   ├── reports.html      # Statistics & reports
│   └── ...
│
└── static/               # Static files (if any)
    ├── css/
    ├── js/
    └── images/
```

---

## 📖 Foydalanish

### 1. Dashboard
- Bugungi davomatning umumiy ko'rinishi
- Statistika kartalar
- Tezkor harakatlar

### 2. Guruhlar va Talabalar (Admin Panel)
- **Guruh qo'shish**: Yangi guruh yaratish
- **Talaba qo'shish**: Ism, familiya va guruh kiritish
- **O'chirish**: Soft delete (ma'lumotlar saqlanadi)
- **Tahrirlash**: Ma'lumotlarni yangilash

### 3. Davomat Belgilash
- Guruhni tanlash
- Sanani tanlash (default: bugun)
- Har bir talaba uchun "Keldi" yoki "Kelmadi" belgilash
- Saqlash

### 4. Hisobotlar
- Sana bo'yicha filtrlash (bugun, kecha, 7 kun, 30 kun)
- Umumiy statistika (kelgan, kelmagan, foiz)
- Guruhlar bo'yicha tahlil
- Kunlik tafsilotlar

---

## 🌐 Production'ga Deploy qilish

Batafsil ko'rsatma: [DEPLOYMENT.md](DEPLOYMENT.md)

### Qisqacha:

1. **GitHub'ga yuklash**
```bash
git push origin main
```

2. **Render.com'da deploy**
- Repository'ni ulash
- Environment variables qo'shish
- Deploy qilish

3. **Tekshirish**
- URL'ni oching
- Login qiling
- Funksionallikni test qiling

---

## 🔒 Xavfsizlik

### Production uchun:

1. **SECRET_KEY o'zgartiring**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Admin parolini o'zgartiring**
`auth.py` faylida:
```python
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password_hash': generate_password_hash('YANGI_QATTIQ_PAROL')
}
```

3. **HTTPS ishlatiladi** (Render/Railway avtomatik)

4. **Environment variables** kodda emas, `.env` da

---

## 🐛 Muammolarni Hal Qilish

### Database topilmadi
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### Module not found
```bash
pip install -r requirements.txt
```

### Port band
```bash
# Boshqa port ishlatish
flask run --port 5001
```

---

## 🤝 Hissa qo'shish

1. Fork qiling
2. Feature branch yarating (`git checkout -b feature/AmazingFeature`)
3. Commit qiling (`git commit -m 'Add some AmazingFeature'`)
4. Push qiling (`git push origin feature/AmazingFeature`)
5. Pull Request oching

---

## 📝 License

MIT License - batafsil [LICENSE](LICENSE) faylida

---

## 👨‍💻 Muallif

**O'zingizning ismingiz**
- GitHub: [@username](https://github.com/username)
- Email: your.email@example.com

---

## 🙏 Minnatdorchilik

- Flask community
- SQLAlchemy documentation
- Render.com & Railway.app

---

## 📞 Support

Savollar yoki muammolar bo'lsa:
- Issues: [GitHub Issues](https://github.com/username/attendance-system/issues)
- Email: support@example.com

---

## 🔄 Changelog

### Version 1.0.0 (2025-01-10)
- ✅ Initial release
- ✅ Davomat belgilash funksiyasi
- ✅ Guruhlar va talabalar boshqaruvi
- ✅ Hisobotlar va statistika
- ✅ Responsive dizayn
- ✅ Admin authentication

---

## 🎯 Kelajak Rejalari

- [ ] Talaba uchun shaxsiy kabinet
- [ ] Email notification'lar
- [ ] Excel export
- [ ] QR code attendance
- [ ] Multi-language support
- [ ] Dark mode

---

**Loyihani yoqtirdingizmi? ⭐ Star bering!**
