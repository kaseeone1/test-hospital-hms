import sqlite3

db_path = 'instance/bluwik_hms.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()

print("users table columns:")
for col in columns:
    print(col)

conn.close() 