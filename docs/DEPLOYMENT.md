# 🌐 מדריך Deployment

## Overview

This guide covers deploying the Queue System to Render.com with persistent storage.

---

## Platform: Render.com

### Why Render?
- Free tier available
- Automatic SSL
- Persistent disk for database
- Easy Git integration
- PostgreSQL/SQLite support

---

## Prerequisites

1. **Render Account** - Sign up at render.com
2. **Git Repository** - Code must be in GitHub/GitLab
3. **Current Project** - All files committed

---

## Step 1: Prepare for Deployment

### 1.1 Update Procfile
```
web: gunicorn app:app
```

### 1.2 Verify requirements.txt
```txt
Flask==3.0.0
Flask-CORS==4.0.0
Werkzeug==3.0.0
gunicorn==21.2.0
```

### 1.3 Update app.py Database Path
```python
if os.path.exists('/var/data'):
    DB_FILE = '/var/data/queue_system.db'
    LOG_FILE = '/var/data/queue_system.log'
else:
    DB_FILE = 'queue_system.db'
    LOG_FILE = 'queue_system.log'
```

### 1.4 Ensure config.json Exists
```bash
git add config.json
git commit -m "Add config for deployment"
```

---

## Step 2: Setup Render Service

### 2.1 Create Web Service
1. Log in to render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Fill in details:
   - **Name**: `queue-system`
   - **Region**: Choose closest region
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

---

## Step 3: Configure Environment

### 3.1 Environment Variables
In Render dashboard → Settings → Environment:

```
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### 3.2 Persistent Disk Setup
1. In Render dashboard → Disks
2. Click "Add Disk"
3. Configure:
   - **Name**: `queue-data`
   - **Mount Path**: `/var/data`
   - **Size**: 1 GB (or more)

---

## Step 4: Deploy

### 4.1 Automatic Deployment
Push to GitHub:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

Render will auto-deploy on push.

### 4.2 Monitor Deployment
1. View deploy logs in Render dashboard
2. Check for errors in "Logs" section

### 4.3 Access Your App
```
https://queue-system-qw88.onrender.com
```

---

## Step 5: Post-Deployment

### 5.1 Update CORS in app.py
```python
cors_config = {
    "origins": [
        "https://queue-system-qw88.onrender.com",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ],
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Content-Type"]
}
```

### 5.2 Test API
```bash
curl https://queue-system-qw88.onrender.com/api/center-data
```

### 5.3 Access Logs
View in Render dashboard → Logs section

---

## Step 6: Backup & Maintenance

### 6.1 Database Backup
Manual backup from Render persistent disk:
```bash
# In production, download via Render dashboard
```

### 6.2 Monitor Disk Space
- Render shows disk usage in dashboard
- Add logs cleanup if needed

### 6.3 Update Dependencies
```bash
pip list --outdated
pip install --upgrade [package]
git push
```

---

## Troubleshooting Deployment

| Problem | Solution |
|---------|----------|
| "Build failed" | Check `pip install` output in logs |
| "No module named 'flask'" | Ensure requirements.txt installed |
| "500 Server Error" | Check logs, restart service |
| "Database locked" | Reduce concurrent requests, use WAL |
| "Static files not loading" | Copy to `/static` + serve properly |
| "CORS errors" | Update cors_config with domain |

---

## Performance Tuning

### 1. Database Optimization
```python
# In app.py, after connection:
conn.execute("PRAGMA journal_mode=WAL")
```

### 2. Gunicorn Workers
```
gunicorn app:app --workers 4 --worker-class sync --timeout 60
```

### 3. Caching
Implement Redis for session caching (future enhancement)

---

## Monitoring & Alerts

### Setup Render Alerts
1. Dashboard → Settings → Alerts
2. Notify on:
   - Build failures
   - Service crashes
   - High error rates

### View Metrics
- CPU/Memory usage in dashboard
- Request rate
- Error rate

---

## Database Persistence

### SQLite in Production
- Works on Render persistent disk
- Limited to ~1GB for free tier
- Better performance than PostgreSQL for small-medium scale

### If Need PostgreSQL
1. Click "New +" → "PostgreSQL"
2. Update connection string in app.py
3. Replace SQLite with psycopg2

---

## Scaling (Future)

When you need to scale:

1. **Load Balancer** - Render handles automatically
2. **Database** - Upgrade to PostgreSQL + Render Geo
3. **Cache** - Add Redis for sessions
4. **CDN** - Use Cloudflare for frontend

---

## Rollback Plan

If deployment fails:

1. **Automatic**: Render keeps previous version
2. **Manual**: Use Render dashboard → Settings → Revert
3. **Git**: `git revert [commit]` + push

---

## Security Checklist

- [ ] CORS configured correctly
- [ ] Security headers enabled
- [ ] Environment variables protected
- [ ] Database backups scheduled
- [ ] Logs retention set
- [ ] HTTPS enforced
- [ ] SSH keys for Git added

---

## Support URLs

- **App**: https://queue-system-qw88.onrender.com
- **Render Docs**: render.com/docs
- **Flask Docs**: flask.palletsprojects.com
- **Gunicorn Docs**: gunicorn.org

---

## Next Steps

- [ ] Setup automatic backups
- [ ] Configure email notifications
- [ ] Add health check endpoint
- [ ] Monitor error rates
- [ ] Plan scaling strategy
