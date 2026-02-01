"""
Test script to debug folder auto-scan issues
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 70)
print("ChromaCloud - Folder Auto-Scan Debug Test")
print("=" * 70)

# Test 1: Import modules
print("\n[Test 1] Importing modules...")
try:
    from CC_Database import CC_Database
    from CC_FolderWatcher import CC_FolderWatcher
    from CC_AutoAnalyzer import CC_AutoAnalyzer
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Create test database
print("\n[Test 2] Creating test database...")
try:
    db = CC_Database(Path("test_debug.db"))
    print("✓ Database created")

    # Create a test folder album
    album_id = db.create_album("Test_Folder_Album", "Test")
    print(f"✓ Created album with ID: {album_id}")

    # Set it as a folder album
    cursor = db.conn.cursor()
    cursor.execute(
        "UPDATE albums SET folder_path = ?, auto_scan = 1 WHERE id = ?",
        (str(Path.home()), album_id)
    )
    db.conn.commit()
    print("✓ Updated album as folder album")

    # Test adding a photo
    test_photo = Path(__file__)  # Use this script as a test "photo"
    photo_id = db.add_photo(test_photo)
    print(f"✓ Added test photo with ID: {photo_id}")

    # Add photo to album
    db.add_photo_to_album(photo_id, album_id)
    print(f"✓ Added photo to album")

    # Query album photos
    photos = db.get_album_photos(album_id)
    print(f"✓ Album contains {len(photos)} photo(s)")

    for photo in photos:
        print(f"  - Photo ID: {photo['id']}, Path: {photo['file_path']}")

    # Cleanup
    db.close()
    Path("test_debug.db").unlink()
    print("✓ Cleaned up test database")

except Exception as e:
    print(f"✗ Database test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test CC_FolderWatcher signal emission
print("\n[Test 3] Testing CC_FolderWatcher...")
try:
    from PySide6.QtCore import QCoreApplication, QTimer

    app = QCoreApplication(sys.argv)

    # Create a test folder with the script
    test_folder = Path(__file__).parent

    # Use list to allow modification in nested function
    received_photos = []
    scan_completed = [False]

    def on_photos_found(paths):
        print(f"✓ Signal received: {len(paths)} photos")
        for i, p in enumerate(paths[:5]):  # Show first 5
            print(f"  - {p.name}")
        if len(paths) > 5:
            print(f"  ... and {len(paths) - 5} more")
        received_photos.extend(paths)

    def on_scan_complete(count):
        scan_completed[0] = True
        print(f"✓ Scan complete signal received: {count} photos found")
        # Quit after a delay to allow signal processing
        QTimer.singleShot(500, app.quit)

    watcher = CC_FolderWatcher(test_folder, 1)
    watcher.new_photos_found.connect(on_photos_found)
    watcher.scan_complete.connect(on_scan_complete)

    print(f"Starting watcher for: {test_folder}")

    # Start the watcher AFTER connecting signals
    watcher.start()

    # Run event loop for max 10 seconds
    QTimer.singleShot(10000, lambda: (print("Timeout!"), app.quit()))

    app.exec()

    watcher.stop_watching()
    watcher.wait()

    if len(received_photos) > 0:
        print(f"✓ Watcher successfully emitted {len(received_photos)} photos")
    else:
        print("✗ No photos received from watcher!")

    if scan_completed[0]:
        print("✓ Scan complete signal received")
    else:
        print("✗ Scan complete signal NOT received")

except Exception as e:
    print(f"✗ Watcher test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Debug test complete!")
print("=" * 70)
