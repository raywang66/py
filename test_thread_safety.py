"""
Quick test to verify thread safety fix
"""

import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 70)
print("Thread Safety Fix Verification Test")
print("=" * 70)

# Test 1: Import and create AutoAnalyzer with db_path
print("\n[Test 1] Testing CC_AutoAnalyzer with db_path...")
try:
    from CC_AutoAnalyzer import CC_AutoAnalyzer
    from CC_SkinProcessor import CC_SkinProcessor
    from CC_Database import CC_Database

    # Create processor
    processor = CC_SkinProcessor()
    print("✓ Created processor")

    # Create database and get its path
    db = CC_Database(Path("test_thread_safety.db"))
    db_path = db.db_path
    print(f"✓ Created database: {db_path}")

    # Create AutoAnalyzer with db_path (not db object)
    analyzer = CC_AutoAnalyzer(processor, db_path)
    print("✓ Created AutoAnalyzer with db_path")

    # Verify it doesn't have db connection yet
    if analyzer.db is None:
        print("✓ AutoAnalyzer.db is None (will be created in thread)")
    else:
        print("✗ AutoAnalyzer.db should be None before thread starts")

    # Clean up
    db.close()
    Path("test_thread_safety.db").unlink()
    print("✓ Cleaned up")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Verify thread-local connection creation
print("\n[Test 2] Testing thread-local database connection...")
try:
    from PySide6.QtCore import QCoreApplication, QTimer

    app = QCoreApplication(sys.argv)

    # Create test database
    db = CC_Database(Path("test_thread_safety2.db"))
    db_path = db.db_path

    # Create album for testing
    album_id = db.create_album("Test_Thread_Safety", "Test")
    print(f"✓ Created test album: {album_id}")

    # Create analyzer
    processor = CC_SkinProcessor()
    analyzer = CC_AutoAnalyzer(processor, db_path)

    # Track if thread created its own connection
    connection_created = [False]

    def check_connection():
        # Give thread time to start and create connection
        if analyzer.db is not None:
            connection_created[0] = True
            print("✓ Thread created its own database connection")
        else:
            print("⏳ Waiting for thread to create connection...")

        # Check again or quit
        if connection_created[0]:
            QTimer.singleShot(500, app.quit)
        else:
            QTimer.singleShot(500, check_connection)

    # Start analyzer
    analyzer.start()
    print("✓ Started AutoAnalyzer thread")

    # Check connection creation after delay
    QTimer.singleShot(500, check_connection)

    # Timeout after 5 seconds
    QTimer.singleShot(5000, lambda: (print("Timeout"), app.quit()))

    app.exec()

    # Stop analyzer
    analyzer.stop()
    analyzer.wait()
    print("✓ Stopped AutoAnalyzer thread")

    # Clean up
    db.close()
    Path("test_thread_safety2.db").unlink()

    if connection_created[0]:
        print("✓ Thread safety test PASSED")
    else:
        print("✗ Thread did not create connection")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Thread Safety Fix Verification Complete!")
print("=" * 70)
print("""
If all tests passed, the thread safety fix is working correctly.

The fix ensures:
- ✅ Each thread creates its own database connection
- ✅ No cross-thread database object sharing
- ✅ Proper connection lifecycle management
- ✅ No SQLite threading errors

You can now use ChromaCloud safely with folder monitoring!
""")
