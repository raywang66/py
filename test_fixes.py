"""
Test the fixes for database-only loading and orphaned thumbnail cleanup
"""
import sqlite3
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from CC_Database import CC_Database

print("="*70)
print("TESTING FIXES FOR DATABASE LOGIC")
print("="*70)

db_path = Path("C:/Users/rwang/lc_sln/py/chromacloud.db")

# Check before
print("\nBEFORE FIX:")
print("-" * 70)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM photos")
photos_count = cursor.fetchone()[0]
print(f"Photos in database: {photos_count}")

cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
cache_count = cursor.fetchone()[0]
print(f"Thumbnail cache entries: {cache_count}")

conn.close()

# Test get_all_photos()
print("\nTEST 1: get_all_photos() method")
print("-" * 70)
db = CC_Database(db_path)
all_photos = db.get_all_photos()
print(f"db.get_all_photos() returned: {len(all_photos)} photos")
print(f"Expected: 0 photos (database is empty)")
if len(all_photos) == 0:
    print("PASS: Returns empty list when database has no photos")
else:
    print("FAIL: Should return empty list!")

# Test orphaned thumbnail cleanup
print("\nTEST 2: Orphaned thumbnail cleanup")
print("-" * 70)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
cache_after = cursor.fetchone()[0]
conn.close()

print(f"Thumbnail cache entries after cleanup: {cache_after}")
print(f"Expected: 0 (all should be deleted as orphans)")
if cache_after == 0:
    print("PASS: All orphaned thumbnails cleaned up")
else:
    print(f"FAIL: Still have {cache_after} orphaned cache entries!")

db.close()

# Summary
print("\n" + "="*70)
print("SUMMARY OF FIXES:")
print("="*70)
print("""
FIX 1: _load_all_photos() now uses database
   - Changed from: Scanning file system (Photos folder)
   - Changed to: Query database (db.get_all_photos())
   - Result: Only shows photos that have been explicitly added

FIX 2: Automatic orphaned thumbnail cleanup
   - Added: cleanup_orphaned_thumbnails() method
   - Called: On database initialization
   - Result: Removes cache entries without corresponding photos

EXPECTED BEHAVIOR:
   When you click "All Photos" -> Shows 0 photos (database is empty)
   When you create an Album -> Shows 0 photos (no photos added yet)
   When you add photos -> They appear in database AND UI
""")

print("\nYou can now run CC_Main.py and verify:")
print("   1. Click 'All Photos' -> Should show 0 photos")
print("   2. Create a new Album -> Should show 0 photos")
print("   3. Add photos to an Album -> They appear in the Album")
print("   4. Click 'All Photos' again -> Should show all added photos")
