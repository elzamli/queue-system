import sqlite3

conn = sqlite3.connect('queue_system.db')
cursor = conn.cursor()

cursor.execute('SELECT id, station_id, customer_number, status FROM queue_entries')
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()