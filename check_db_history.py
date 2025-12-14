
import sqlite3
conn = sqlite3.connect('queue_system.db')
cursor = conn.cursor()

# ספור כמה רשומות יש
cursor.execute('SELECT COUNT(*) FROM queue_entries_history')
count = cursor.fetchone()[0]
print(f'Total history records: {count}')

# ראה את ה-5 האחרונים
cursor.execute('''
    SELECT customer_number, station_name, status, action, created_at
    FROM queue_entries_history
    ORDER BY created_at DESC
    LIMIT 5
''')

for row in cursor.fetchall():
    print(row)

conn.close()