"""Verify Photos folder vs Database"""
from pathlib import Path
import sqlite3

# Count files in Photos directory (same logic as CC_Main._load_all_photos)
photos_dir = Path(__file__).parent / "Photos"
extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG', '*.arw', '*.nef', '*.cr2', '*.cr3', '*.dng']

photos = []
for ext in extensions:
    photos.extend(photos_dir.glob(ext))

print("="*70)
print("📁 FILE SYSTEM (Photos folder - root directory only)")
print("="*70)
print(f"Total photos in Photos root directory: {len(photos)}")
print(f"\nFirst 5 photos:")
for photo in sorted(photos)[:5]:
    print(f"  - {photo.name}")
print(f"...")

# Check database
db_path = Path(__file__).parent / "chromacloud.db"
print("\n" + "="*70)
print("💾 DATABASE (chromacloud.db)")
print("="*70)

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count albums
    cursor.execute("SELECT COUNT(*) FROM albums")
    album_count = cursor.fetchone()[0]
    print(f"Albums: {album_count}")

    # Count photos in database
    cursor.execute("SELECT COUNT(*) FROM photos")
    db_photo_count = cursor.fetchone()[0]
    print(f"Photos in database: {db_photo_count}")

    # Count thumbnail cache
    cursor.execute("SELECT COUNT(*) FROM thumbnail_cache")
    cache_count = cursor.fetchone()[0]
    print(f"Thumbnail cache entries: {cache_count}")

    conn.close()
else:
    print("Database does not exist!")

print("\n" + "="*70)
print("📊 EXPLANATION")
print("="*70)
print("""
When you click "All Photos" in CC_Main.py:
  → It scans the Photos FOLDER (file system)
  → NOT the database!
  
When you click an Album:
  → It queries the DATABASE
  → NOT the file system!
  
This is why you see 157 photos even though the database is empty.
The 157 photos are actual files in your Photos folder.
""")
