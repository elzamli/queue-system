# 🗄️ סכימת בסיס הנתונים

## סקירה כללית

בסיס הנתונים אחסן בקובץ `queue_system.db` (SQLite) וכולל 4 טבלות ראשיות:

---

## טבלה 1: `stations` - התחנות/הדלפקים

```sql
CREATE TABLE stations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,                -- שם התחנה (גם בעברית)
    description TEXT,                         -- תיאור התחנה
    current_number INTEGER DEFAULT 0,         -- מספר לקוח בשירות כרגע
    queue_group_id TEXT DEFAULT NULL,         -- איד של קבוצת תור (עבור תחנות משותפות)
    is_routing INTEGER DEFAULT 0,             -- האם מנתב לקוח בין תחנות
    is_active INTEGER DEFAULT 1,              -- פעילה או לא
    hidden INTEGER DEFAULT 0,                 -- הסתרה מהתצוגה
    restricted INTEGER DEFAULT 0,             -- מוגבלת או לא
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### דוגמה:
```json
{
  "id": 1,
  "name": "אש-חתם עמ' 1",
  "description": "אש-חתם",
  "queue_group_id": "esh_hatam",
  "hidden": 0,
  "restricted": 0
}
```

---

## טבלה 2: `queue_entries` - רשימת הלקוחות

```sql
CREATE TABLE queue_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id INTEGER NOT NULL,              -- איד התחנה
    customer_number INTEGER NOT NULL,         -- מספר הלקוח הייחודי
    status TEXT DEFAULT 'waiting',            -- 'waiting', 'called', 'completed'
    position INTEGER DEFAULT 0,               -- מיקום בתור
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- זמן הכנסה לתור
    called_at TIMESTAMP,                      -- זמן קריאה
    completed_at TIMESTAMP,                   -- זמן סיום שירות
    finished_at TIMESTAMP,                    -- זמן סיום (דומה ל-completed)
    released_at TIMESTAMP,                    -- זמן שחרור (ייצור שנוי)
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

### States:
- `waiting` - בהמתנה לקריאה
- `called` - בשירות ברגע זה
- `completed` - סיים שירות

---

## טבלה 3: `operators` - מפעילים/קוד הזדהות

```sql
CREATE TABLE operators (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,                -- קוד מזדהה יחודי (למשל: "1001")
    station_id INTEGER DEFAULT NULL,          -- איד התחנה שבה הוא עובד
    name TEXT NOT NULL,                       -- שם המפעיל
    finish_operator INTEGER DEFAULT 0,        -- האם מפעיל סיום שירות
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

### דוגמה:
```json
{
  "id": 1,
  "code": "1001",
  "station_id": 1,
  "name": "דוד",
  "finish_operator": 0
}
```

---

## טבלה 4: `queue_entries_history` - היסטוריית פעולות

```sql
CREATE TABLE queue_entries_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_number INTEGER NOT NULL,         -- מספר הלקוח
    station_id INTEGER NOT NULL,              -- איד התחנה
    station_name TEXT NOT NULL,               -- שם התחנה
    status TEXT NOT NULL,                     -- הסטטוס במומנט הפעולה
    action TEXT,                              -- תיאור הפעולה
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### דוגמה:
```json
{
  "customer_number": 101,
  "station_id": 1,
  "station_name": "אש-חתם עמ' 1",
  "status": "called",
  "action": "called_by_operator_1001"
}
```

---

## Relationships

```
stations (1) ──→ (N) queue_entries
  ↓
operators ──→ stations
  ↓
queue_entries_history ──→ stations & queue_entries
```

---

## Thread Safety

- `db_lock` משמרת critical sections
- כל שינוי מכונה עם lock
- Connection per request pattern

---

## טעינה ראשונית

בעת הפעלה:
1. אתחול טבלות אם אינן קיימות
2. טעינת stations מ-config.json
3. טעינת operators מ-config.json
4. רישום ב-log

---

## Indexes (ממליצים להוסיף):

```sql
CREATE INDEX idx_queue_entries_station ON queue_entries(station_id);
CREATE INDEX idx_queue_entries_status ON queue_entries(status);
CREATE INDEX idx_queue_entries_customer ON queue_entries(customer_number);
CREATE INDEX idx_entries_history_customer ON queue_entries_history(customer_number);
CREATE INDEX idx_operators_code ON operators(code);
```
