#!/bin/bash

# ❌ בדיקה אם Python מותקן
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 לא מותקן. אנא התקן Python 3.8 או גרסה חדשה יותר"
    exit 1
fi

echo "✅ Python 3 מזוהה"

# התקנת דרישות
echo "📦 התקנת דרישות..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ שגיאה בהתקנת דרישות"
    exit 1
fi

echo "✅ דרישות הותקנו בהצלחה"

# הפעלת השרת
echo ""
echo "🚀 הפעלת מערכת ניהול התורים..."
echo "🌐 הגש אל http://localhost:5000"
echo "⏹️  לעצירה, לחץ Ctrl+C"
echo ""

python3 app.py
