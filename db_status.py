import sqlite3

conn = sqlite3.connect("chromacloud.db")
cursor = conn.cursor()

print("DATABASE STATUS")
print("=" * 40)

cursor.execute("SELECT COUNT(*) FROM photos")
print(f"photos:           {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM albums")
print(f"albums:           {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
print(f"thumbnail_cache:  {cursor.fetchone()[0]}")

conn.close()
