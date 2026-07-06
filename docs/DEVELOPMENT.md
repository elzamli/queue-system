# 🚀 מדריך פיתוח

## Requirements

- Python 3.8+
- pip
- Git (אופציונלי)

---

## 1️⃣ Setup Local Environment

### Step 1: Clone / Download
```bash
cd queue_system
```

### Step 2: Create Virtual Environment (מומלץ)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 2️⃣ Configuration

### config.json Structure

```json
{
  "stations": [
    {
      "id": 1,
      "name": "Station Name",
      "description": "Description",
      "queue_group_id": null,
      "hidden": 0,
      "restricted": 0,
      "is_routing": 0
    }
  ],
  "operators": [
    {
      "id": 1,
      "code": "1001",
      "station_id": 1,
      "name": "Operator Name",
      "finish_operator": 0
    }
  ]
}
```

---

## 3️⃣ Running the App

### Locally (Development)
```bash
python app.py
```

Access at: `http://localhost:5000`

### Using run.bat (Windows)
```bash
run.bat
```

### Using run.sh (macOS/Linux)
```bash
bash run.sh
```

---

## 4️⃣ Database Management

### View Database
```bash
python show_db.py
```

### Reset Database (Advanced)
```bash
python
>>> import os
>>> os.remove('queue_system.db')
>>> exit()
# Then restart app.py
```

---

## 5️⃣ Testing

### Load Testing
```bash
python load_test.py
```

Tests concurrent requests to:
- Add Customer
- Search Customer
- Center Data
- Call Next

### Test Configuration
Edit `load_test.py`:
```python
CONCURRENT_REQUESTS = 20  # בקשות בו-זמנית
ITERATIONS = 5            # מספר rounds
BASE_URL = "http://127.0.0.1:5000/"
```

---

## 6️⃣ File Structure

```
app.py              # Main Flask app
├── init_db()       # Database initialization
├── get_db_connection()  # DB connection helper
├── Routes ('/') – Web pages
├── API Endpoints ('/api/*') – JSON responses
└── log_action()    # Logging

templates/          # HTML files
├── center.html     # Dashboard
├── operator.html   # Operator panel
├── admin.html      # Admin panel
└── ...

config.json         # Station & operator config
queue_system.db     # SQLite database (auto-created)
queue_system.log    # Log file (auto-created)
```

---

## 7️⃣ Key Functions

### `init_db()`
Initialize database with stations & operators from config.json

### `get_db_connection()`
Get safe SQLite connection

### `log_action(action, details, level)`
Log to file + console

### `log_to_history(cursor, customer_number, ...)`
Record action in history table

### API Endpoints
- `@app.route()` - Web pages
- `@app.route('/api/*')` - JSON API

---

## 8️⃣ Common Development Tasks

### Add New Station
Edit `config.json`:
```json
{
  "id": 99,
  "name": "New Station",
  "description": "Description",
  "queue_group_id": null,
  "hidden": 0,
  "restricted": 0,
  "is_routing": 0
}
```

Then restart app.

### Add New Operator
Edit `config.json`:
```json
{
  "id": 99,
  "code": "9999",
  "station_id": 1,
  "name": "Operator Name",
  "finish_operator": 0
}
```

### Enable Admin Panel
Currently uses simple password check. Modify `/api/admin/verify` endpoint.

### Change Database Location
Edit `app.py`:
```python
DB_FILE = '/var/data/queue_system.db'  # Render persistent
# or
DB_FILE = 'queue_system.db'  # Local
```

---

## 9️⃣ Debug Mode

### Flask Debug
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### Console Logging
All `log_action()` calls print to console

### View Logs
```bash
tail -f queue_system.log
```

---

## 🔟 ENV Variables (Render Deployment)

```bash
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

---

## Tools Used

| Tool | Purpose |
|------|---------|
| Flask | Web framework |
| Flask-CORS | Cross-origin requests |
| Werkzeug | Security hashing |
| SQLite3 | Database |
| Gunicorn | WSGI server (production) |
| threading | Thread safety |
| logging | File logging |

---

## Performance Tips

1. Add database indexes (see DATABASE.md)
2. Implement connection pooling
3. Cache center-data if refresh rate > 1sec
4. Use middleware for request logging
5. Optimize queue queries with LIMIT clauses

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Database locked" | Increase db_lock timeout or use WAL mode |
| Port 5000 in use | `lsof -i :5000` then kill process |
| Import errors | `pip install -r requirements.txt` |
| Hebrew chars broken | Ensure UTF-8 encoding in files |
| CORS errors | Check cors_config in app.py |

---

## Next Steps

- [ ] Add authentication (JWT)
- [ ] Implement WebSocket for real-time updates
- [ ] Add database backup schedule
- [ ] Create admin dashboard
- [ ] Add SMS/Email notifications
- [ ] Implement duty roster
