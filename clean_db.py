import sqlite3

conn = sqlite3.connect('queue_system.db')
cursor = conn.cursor()

# מחק את כל entries
cursor.execute('DELETE FROM queue_entries')

# וודא
cursor.execute('SELECT * FROM queue_entries')
result = cursor.fetchall()

print(f'Entries remaining: {len(result)}')
print('✅ Database cleaned!')

conn.commit()
conn.close()