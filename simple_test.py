import sqlite3
from pathlib import Path

db_path = Path("C:/Users/rwang/lc_sln/py/chromacloud.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Database status:")
cursor.execute("SELECT COUNT(*) FROM photos")
print(f"  photos: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
print(f"  thumbnail_cache: {cursor.fetchone()[0]}")

conn.close()

# Import and test
import sys
sys.path.insert(0, "C:/Users/rwang/lc_sln/py")
from CC_Database import CC_Database

print("\nInitializing database (will clean orphans)...")
db = CC_Database(db_path)

print("\nAfter cleanup:")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
print(f"  thumbnail_cache: {cursor.fetchone()[0]}")
conn.close()

print("\nTesting get_all_photos()...")
photos = db.get_all_photos()
print(f"  Result: {len(photos)} photos")

db.close()
print("\nDone!")
