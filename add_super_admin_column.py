import sqlite3

db_path = 'instance/bluwik_hms.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT 0;")
    print("Column is_super_admin added successfully.")
except Exception as e:
    print(f"Error: {e}")

conn.commit()
conn.close() 