import sqlite3
from datetime import datetime, timedelta

def convert_utc_to_ist(dt_str):
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        dt_ist = dt + timedelta(hours=5, minutes=30)
        return dt_ist.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return dt_str

db_path = 'database/db.sqlite3'

tables = [
    ('users', 'created_at'),
    ('merchants', 'created_at'),
    ('transactions', 'created_at'),
    ('otps', 'created_at')
]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for table, col in tables:
    cursor.execute(f"SELECT id, {col} FROM {table}")
    rows = cursor.fetchall()
    for row in rows:
        row_id, old_time = row
        if old_time:
            new_time = convert_utc_to_ist(old_time)
            cursor.execute(f"UPDATE {table} SET {col} = ? WHERE id = ?", (new_time, row_id))

conn.commit()
conn.close()
print('All UTC timestamps converted to IST.') 