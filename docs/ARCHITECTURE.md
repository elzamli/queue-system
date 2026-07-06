# 🏗️ ארכיטקטורה המערכת

## סקירה כללית

מערכת ניהול תורים היא יישום Flask מלא מעמד Render עם:
- **Frontend**: HTML/CSS/JavaScript עם רענון אוטומטי
- **Backend**: Python Flask עם API RESTful
- **Database**: SQLite עם thread-safety
- **Deployment**: Render.com עם persistent disk

---

## מבנה היישום

```
queue_system/
├── app.py                    # יישום Flask - נקודת הכניסה
├── config.json              # הגדרות: תחנות וקודי מפעילים
├── requirements.txt         # תלויות Python
├── templates/               # HTML פיתוח
│   ├── center.html         # דשבורד מרכזי
│   ├── stations.html       # תצוגת תחנות
│   ├── operator.html       # ממשק מפעיל
│   ├── finish.html         # סיום שירות
│   ├── admin.html          # ניהול מערכת
│   └── add_customer.html   # הזנת לקוחות
└── load_test.py            # בדיקת עומס
```

---

## זרימת הנתונים

```
┌─────────────────────┐
│   Frontend (HTML)   │
│  - Center Screen    │
│  - Add Customer     │
│  - Operator Panel   │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Flask Backend      │
│  - API Endpoints    │
│  - Business Logic   │
│  - Authorization    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   SQLite Database   │
│  - stations         │
│  - queue_entries    │
│  - operators        │
│  - history          │
└─────────────────────┘
```

---

## רכיבים עיקריים

### 1. **Database Layer** (`init_db()`)
- אתחול טבלות SQLite
- טעינת נתונים מ-config.json
- thread-safe עם locks

### 2. **API Endpoints**
- **תצוגה**: `/`, `/stations`, `/operator/<id>`
- **נתונים**: `/api/center-data`, `/api/get-station/<id>`
- **פעולות**: `/api/add-entry`, `/api/call-next/<id>`, `/api/finish-customer`
- **ניהול**: `/api/admin/*`

### 3. **Security**
- CORS מחוץ
- Security headers
- הוידאות מפעילים

### 4. **Logging**
- logging.py עם timestamp
- רישום פעולות ב-history
- שמירה ל-file וקונסול

---

## Pattern: Queue Group

- תחנות בעלות אותו `queue_group_id` חולקות תור אחד
- דיספליי מרכזי מציג קבוצה אחת בפעם

---

## סטוקים (Stack)

- **Frontend**: HTML5, CSS3, JavaScript Fetch
- **Backend**: Flask 3.0.0, Flask-CORS, Werkzeug
- **Database**: SQLite3
- **Server**: Gunicorn (Render)
- **Security**: Werkzeug hash functions

---

## נקודות הרחבה

1. **Authentication** - כרגע רק קוד מפעיל
2. **Real-time Updates** - WebSocket עם SocketIO אפשרי
3. **Performance** - Caching, Database Indexing
4. **Reporting** - ניתוח נתונים מפורטים more detailed analytics
