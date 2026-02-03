import sqlite3
from pathlib import Path

db_path = Path("C:/Users/rwang/lc_sln/py/chromacloud.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Database tables and counts:")
print("-" * 40)

tables = ['albums', 'photos', 'album_photos', 'thumbnail_cache', 'folder_structure']
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:20s}: {count:5d} rows")
    except:
        print(f"{table:20s}: (table doesn't exist)")

conn.close()
