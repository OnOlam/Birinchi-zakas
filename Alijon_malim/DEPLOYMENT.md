# 🚀 Deployment Guide - Davomat Tizimi

Bu qo'llanma Flask ilovani **Render.com** yoki **Railway.app** ga joylashtirish bo'yicha to'liq ko'rsatmalar beradi.

---

## 📋 Loyiha Tuzilishi

```
attendance-system/
├── app.py                  # Asosiy Flask fayl
├── models.py               # Database modellari
├── auth.py                 # Authentication
├── config.py               # Configuration
├── requirements.txt        # Python kutubxonalar
├── Procfile               # Server buyrug'i
├── runtime.txt            # Python versiyasi
├── .env.example           # Environment o'zgaruvchilar namunasi
├── .gitignore             # Git ignore
├── templates/             # HTML shablonlar
│   ├── login.html
│   ├── dashboard.html
│   ├── admin_panel.html
│   ├── attendance.html
│   └── reports.html
└── static/                # CSS, JS, rasmlar (agar bo'lsa)
```

---

## 🔧 Tayyorgarlik

### 1. Loyihani GitHub'ga yuklash

```bash
# Git repository yaratish
git init
git add .
git commit -m "Initial commit - Attendance System"

# GitHub repository yaratib, ulash
git remote add origin https://github.com/username/attendance-system.git
git branch -M main
git push -u origin main
```

### 2. Environment Variables Tayyorlash

`.env.example` faylini `.env` ga nusxalang va sozlang:

```bash
cp .env.example .env
```

`.env` faylini tahrirlang:
```env
FLASK_ENV=production
SECRET_KEY=your-randomly-generated-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

**SECRET_KEY yaratish:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🌐 Render.com ga Deploy qilish

### Bosqich 1: Render.com'da ro'yxatdan o'tish

1. [render.com](https://render.com) ga kiring
2. GitHub akkauntingiz bilan ro'yxatdan o'ting

### Bosqich 2: Yangi Web Service yaratish

1. **Dashboard** → **New** → **Web Service**
2. GitHub repository'ni tanlang
3. Quyidagi sozlamalarni kiriting:

```
Name: attendance-system
Environment: Python
Region: Singapore (yoki eng yaqin region)
Branch: main
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

### Bosqich 3: Environment Variables qo'shish

**Environment** bo'limida quyidagi o'zgaruvchilarni qo'shing:

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | `your-secret-key-here` |
| `PYTHON_VERSION` | `3.11.7` |

### Bosqich 4: Deploy qilish

- **Create Web Service** tugmasini bosing
- Render avtomatik deploy qiladi (5-10 minut)
- Deploy tugagach URL beriladi: `https://attendance-system.onrender.com`

---

## 🚂 Railway.app ga Deploy qilish

### Bosqich 1: Railway.app'da ro'yxatdan o'tish

1. [railway.app](https://railway.app) ga kiring
2. GitHub bilan login qiling

### Bosqich 2: Yangi Project yaratish

1. **New Project** → **Deploy from GitHub repo**
2. Repository'ni tanlang
3. Railway avtomatik aniqlaydi

### Bosqich 3: Environment Variables

**Variables** bo'limida:

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=8080
```

### Bosqich 4: Deploy Settings

Railway avtomatik deploy qiladi. Agar kerak bo'lsa:

1. **Settings** → **Deploy**
2. **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Bosqich 5: Domain olish

- **Settings** → **Generate Domain**
- URL: `https://attendance-system.up.railway.app`

---

## 🗄️ Database (SQLite)

**Muhim:** SQLite fayli serverda yaratiladi va restart qilinganda **o'chib ketadi**.

### Yechim 1: Persistent Storage (Render)

Render'da **Persistent Disk** qo'shing:
1. **Dashboard** → **Disks** → **Add Disk**
2. Mount Path: `/opt/render/project/src/data`
3. `config.py` da:
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:////opt/render/project/src/data/attendance.db'
```

### Yechim 2: PostgreSQL ishlatish (kelajakda)

Agar katta ma'lumotlar bo'lsa, PostgreSQL'ga o'tish mumkin.

---

## ✅ Deploy Tekshirish

### 1. URL ni oching
```
https://your-app-name.onrender.com
```

### 2. Login qiling
```
Username: admin
Password: admin123
```

### 3. Xatoliklarni tekshirish

**Render Logs:**
- Dashboard → Logs
- Real-time loglarni ko'rish

**Railway Logs:**
- Project → Deployments → View Logs

---

## 🔒 Xavfsizlik

### Production uchun majburiy o'zgarishlar:

1. **SECRET_KEY**: Tasodifiy yarating
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **ADMIN PASSWORD**: `auth.py` da o'zgartiring
```python
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password_hash': generate_password_hash('YANGI_PAROL')
}
```

3. **HTTPS**: Render/Railway avtomatik ta'minlaydi

4. **Environment Variables**: Hech qachon kodga yozmang!

---

## 🐛 Keng Tarqalgan Muammolar

### 1. "Application failed to respond"
**Yechim:** Procfile'ni tekshiring
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### 2. "Module not found"
**Yechim:** `requirements.txt` ni tekshiring
```bash
pip freeze > requirements.txt
```

### 3. Database yo'qoladi
**Yechim:** Persistent Disk qo'shing (yuqorida ko'rsatilgan)

### 4. SECRET_KEY xatosi
**Yechim:** Environment variable qo'shing

---

## 📊 Monitoring

### Render:
- **Metrics** → CPU, Memory, Response time
- **Logs** → Real-time loglar

### Railway:
- **Observability** → Metrics va Logs
- **Usage** → Resource ishlatilishi

---

## 🔄 Yangilanishlar Deploy qilish

### Avtomatik Deploy (GitHub bilan)

```bash
git add .
git commit -m "Feature: yangi funksiya qo'shildi"
git push origin main
```

Render/Railway avtomatik yangi versiyani deploy qiladi.

### Manual Deploy

**Render:** Dashboard → Manual Deploy → Deploy latest commit

**Railway:** Avtomatik deploy (o'chirilgan bo'lsa: Settings → Deploy → Trigger Deploy)

---

## 💡 Tavsiyalar

1. **Backup:** Database'ni muntazam saqlang
2. **Monitoring:** Loglarni kuzatib turing
3. **Testing:** Production'ga yuklashdan oldin test qiling
4. **Documentation:** O'zgarishlarni yozib boring

---

## 📞 Yordam

Muammolar bo'lsa:
- Render: [render.com/docs](https://render.com/docs)
- Railway: [docs.railway.app](https://docs.railway.app)
- Flask: [flask.palletsprojects.com](https://flask.palletsprojects.com)

---

## ✅ Deploy Checklist

- [ ] GitHub repository yaratildi
- [ ] `.env` fayli sozlandi (SECRET_KEY, PASSWORD)
- [ ] `requirements.txt` to'liq
- [ ] `Procfile` mavjud
- [ ] Render/Railway'da project yaratildi
- [ ] Environment variables qo'shildi
- [ ] Deploy muvaffaqiyatli
- [ ] Login ishlayapti
- [ ] Barcha sahifalar ochiladi
- [ ] Database saqlanyapti

---

**Muvaffaqiyatli deploy qiling! 🎉**
