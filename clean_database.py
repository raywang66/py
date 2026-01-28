"""
Clean database - Remove all analysis results
This will clear the analysis_results table to fix data type issues.
Photos and albums will NOT be affected.
"""

import sqlite3
from pathlib import Path

def clean_analysis_results():
    """Clear all analysis results from database"""
    db_path = Path(__file__).parent / "chromacloud.db"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Count existing records
    cursor.execute("SELECT COUNT(*) FROM analysis_results")
    count = cursor.fetchone()[0]

    print(f"📊 Found {count} analysis records")

    if count > 0:
        response = input(f"\n⚠️  Delete all {count} analysis records? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            conn.close()
            return

        # Delete all records
        cursor.execute("DELETE FROM analysis_results")
        conn.commit()

        print(f"✅ Deleted {count} analysis records")
        print("✅ Database cleaned successfully!")
        print("\nℹ️  Your photos and albums are still intact.")
        print("ℹ️  You can now re-analyze your photos and the data will be saved correctly.")
    else:
        print("✅ No analysis records to clean")

    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("ChromaCloud Database Cleaner")
    print("=" * 60)
    print("\nThis will remove all analysis results from the database.")
    print("Photos and albums will NOT be affected.\n")

    clean_analysis_results()

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

