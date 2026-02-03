import sqlite3
from pathlib import Path

db_path = Path("C:/Users/rwang/lc_sln/py/chromacloud.db")

print("=" * 60)
print("CHECKING DATABASE STATUS")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\nBEFORE importing CC_Database:")
cursor.execute("SELECT COUNT(*) FROM photos")
photos_before = cursor.fetchone()[0]
print(f"  photos table: {photos_before} rows")

cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
cache_before = cursor.fetchone()[0]
print(f"  thumbnail_cache: {cache_before} rows")

conn.close()

# Now import and initialize (should trigger cleanup)
import sys
sys.path.insert(0, "C:/Users/rwang/lc_sln/py")

print("\n" + "=" * 60)
print("Importing CC_Database (will auto-cleanup orphans)...")
print("=" * 60)

from CC_Database import CC_Database
db = CC_Database(db_path)

print("\nAFTER CC_Database initialization:")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM photos")
photos_after = cursor.fetchone()[0]
print(f"  photos table: {photos_after} rows")

cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
cache_after = cursor.fetchone()[0]
print(f"  thumbnail_cache: {cache_after} rows")

conn.close()

print("\n" + "=" * 60)
print("TESTING get_all_photos() method:")
print("=" * 60)
photos = db.get_all_photos()
print(f"  db.get_all_photos() returned: {len(photos)} photos")

db.close()

print("\n" + "=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"  Orphaned thumbnails cleaned: {cache_before - cache_after}")
print(f"  Photos in database: {photos_after}")
print(f"  get_all_photos() returns: {len(photos)}")

if cache_after == 0 and len(photos) == 0:
    print("\n  SUCCESS: All fixes working correctly!")
else:
    print(f"\n  WARNING: Expected 0 photos and 0 cache, got {len(photos)} and {cache_after}")

# Write results to file
with open("C:/Users/rwang/lc_sln/py/test_results.txt", "w") as f:
    f.write("DATABASE FIX VERIFICATION\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Before: {cache_before} thumbnail cache entries\n")
    f.write(f"After:  {cache_after} thumbnail cache entries\n")
    f.write(f"Cleaned: {cache_before - cache_after} orphaned entries\n\n")
    f.write(f"Photos in database: {photos_after}\n")
    f.write(f"get_all_photos() returns: {len(photos)}\n\n")

    if cache_after == 0 and len(photos) == 0:
        f.write("STATUS: SUCCESS - All fixes working!\n")
    else:
        f.write(f"STATUS: ISSUE - Expected 0, got {len(photos)} photos and {cache_after} cache\n")

print("\nResults written to: test_results.txt")
