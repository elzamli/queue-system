# 📡 תיעוד API

## סקירה כללית

API RESTful המספק ממשק למערכת ניהול התורים. כל endpoints מופצים ב-`/api/*`

---

## 🔐 Authentication

כרגע, הhidden authentication היא דרך קוד מפעיל:

```javascript
POST /api/get-operator-station
{
  "operator_code": "1001"
}
```

---

## 📋 Endpoints

### 1. **GET `/api/center-data`**
מקבל נתונים לדשבורד המרכזי

**תגובה:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "אש-חתם עמ' 1",
      "current_number": 102,
      "waiting": [103, 104, 105],
      "waiting_count": 3
    }
  ]
}
```

---

### 2. **POST `/api/get-operator-station`**
מחזיר פרטי תחנה של מפעיל

**בקשה:**
```json
{
  "operator_code": "1001"
}
```

**תגובה:**
```json
{
  "success": true,
  "station_id": 1,
  "station_name": "אש-חתם עמ' 1"
}
```

---

### 3. **GET `/api/get-station/<station_id>`**
מקבל תהליכי של תחנה מסוימת

**תגובה:**
```json
{
  "success": true,
  "station": {
    "id": 1,
    "name": "אש-חתם עמ' 1",
    "current_number": 102
  }
}
```

---

### 4. **GET `/api/stations-list`**
מחזיר רשימה של כל התחנות

**תגובה:**
```json
{
  "success": true,
  "stations": [
    {
      "id": 1,
      "name": "אש-חתם עמ' 1",
      "description": "אש-חתם"
    }
  ]
}
```

---

### 5. **POST `/api/add-entry`**
הוסף לקוח חדש לתור

**בקשה:**
```json
{
  "station_id": 1,
  "customer_number": 101,
  "transfer": false
}
```

**תגובה:**
```json
{
  "success": true,
  "message": "לקוח 101 נוסף בהצלחה"
}
```

**Error Cases:**
- `400`: station_id/customer_number חסרים
- `409`: לקוח כבר בתור

---

### 6. **POST `/api/call-next/<station_id>`**
קרא ללקוח הבא בתור

**בקשה:**
```json
{
  "operator_code": "1001"
}
```

**תגובה:**
```json
{
  "success": true,
  "customer_number": 101,
  "message": "לקוח 101 קוראו"
}
```

---

### 7. **POST `/api/finish-customer`**
סיים שירות ללקוח

**בקשה:**
```json
{
  "station_id": 1,
  "customer_number": 101,
  "operator_code": "1001"
}
```

**תגובה:**
```json
{
  "success": true,
  "message": "שירות הסתיים"
}
```

---

### 8. **POST `/api/toggle-station-status/<station_id>`**
הפעל/כבה תחנה

**בקשה:**
```json
{
  "operator_code": "1001"
}
```

**תגובה:**
```json
{
  "success": true,
  "is_active": true
}
```

---

### 9. **POST `/api/insert-customer-at-position`**
הוסף לקוח בעמדה ספציפית בתור

**בקשה:**
```json
{
  "station_id": 1,
  "customer_number": 101,
  "position": 2,
  "transfer": false
}
```

**תגובה:**
```json
{
  "success": true,
  "message": "לקוח הוכנס בעמדה 2"
}
```

---

### 10. **POST `/api/admin/verify`**
אימות ניהל (אם יש פרוטוקול)

**בקשה:**
```json
{
  "password": "admin123"
}
```

**תגובה:**
```json
{
  "success": true,
  "verified": true
}
```

---

### 11. **GET `/api/admin/entries`**
קבל כל רשומות התור (ניהול בלבד)

**Query Parameters:**
- `?limit=100` - הגבל תוצאות
- `?station_id=1` - סנן לפי תחנה

**תגובה:**
```json
{
  "success": true,
  "entries": [
    {
      "id": 1,
      "station_id": 1,
      "customer_number": 101,
      "status": "waiting"
    }
  ]
}
```

---

### 12. **PUT `/api/admin/entries`**
עדכן רשומת תור

**בקשה:**
```json
{
  "entry_id": 1,
  "status": "completed",
  "station_id": 1
}
```

**תגובה:**
```json
{
  "success": true,
  "message": "רשומה עודכנה"
}
```

---

### 13. **DELETE `/api/admin/entries`**
מחק רשומה (ניהול)

**בקשה:**
```json
{
  "entry_id": 1
}
```

**תגובה:**
```json
{
  "success": true,
  "message": "רשומה נמחקה"
}
```

---

### 14. **GET `/api/admin/report`**
דוח מלא של פעילות המערכת

**Query Parameters:**
- `?from_date=2024-01-01`
- `?to_date=2024-01-31`
- `?station_id=1`

**תגובה:**
```json
{
  "success": true,
  "report": {
    "total_customers": 1250,
    "total_served": 1200,
    "average_wait_time": 5.3,
    "by_station": {
      "1": {
        "served": 300,
        "average_time": 4.2
      }
    }
  }
}
```

---

### 15. **POST `/api/admin/toggle-station-visibility/<station_id>`**
הסתר/הצג תחנה בדשבורד

**בקשה:**
```json
{
  "hidden": true
}
```

**תגובה:**
```json
{
  "success": true,
  "hidden": true
}
```

---

## Error Codes

| Code | Message | פתרון |
|------|---------|-------|
| 200  | Success | - |
| 400  | Bad Request | בדוק parameters |
| 401  | Unauthorized | בדוק operator_code |
| 404  | Not Found | תחנה/לקוח לא קיים |
| 409  | Conflict | לקוח כבר בתור |
| 500  | Server Error | צור קשר support |

---

## CORS Headers

```
Access-Control-Allow-Origin: https://queue-system-qw88.onrender.com, http://localhost:5000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type
```

---

## Rate Limiting

כרגע: ללא rate limiting מוגדר (ניתן להוסיף ב-Flask)

---

## Version

- API Version: 1.0
- Last Updated: 2024
