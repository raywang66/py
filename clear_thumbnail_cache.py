#!/usr/bin/env python3
"""
Clear thumbnail cache to regenerate at max size (400px)

Run this script to clear old cached thumbnails so they will be
regenerated at the new maximum size of 400px for better zoom quality.
"""

import sys
import sqlite3
from pathlib import Path

def clear_thumbnail_cache(db_path: str):
    """Clear all thumbnail cache from database"""
    print(f"📦 Opening database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current cache size
    cursor.execute("SELECT COUNT(*), SUM(LENGTH(thumbnail_data)) FROM thumbnail_cache")
    count, total_size = cursor.fetchone()

    if count == 0:
        print("✅ No cached thumbnails found")
        conn.close()
        return

    print(f"📊 Current cache:")
    print(f"   • Count: {count} thumbnails")
    print(f"   • Size: {total_size / 1024 / 1024:.2f} MB")

    # Ask for confirmation
    response = input(f"\n⚠️  Delete all {count} cached thumbnails? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        conn.close()
        return

    # Delete all cached thumbnails
    cursor.execute("DELETE FROM thumbnail_cache")
    conn.commit()

    # Vacuum to reclaim space
    print("🧹 Vacuuming database...")
    cursor.execute("VACUUM")

    print(f"✅ Deleted {count} cached thumbnails")
    print("✅ Thumbnails will be regenerated at 400px on next load")

    conn.close()

if __name__ == "__main__":
    # Try to find database
    possible_paths = [
        Path.home() / "CC" / "chromacloud.db",  # macOS
        Path(__file__).parent / "chromacloud.db",  # Windows/Linux
        Path(__file__).parent / "chromacloud-01.db",  # Alternate
    ]

    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = str(path)
            break

    if not db_path:
        print("❌ Could not find chromacloud.db")
        print("   Searched:")
        for path in possible_paths:
            print(f"   • {path}")
        sys.exit(1)

    clear_thumbnail_cache(db_path)

