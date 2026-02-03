"""
Check for duplicate analysis records in database
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "chromacloud.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check for duplicate analysis
cursor.execute("""
    SELECT photo_id, COUNT(*) as count
    FROM analysis_results
    GROUP BY photo_id
    HAVING COUNT(*) > 1
    ORDER BY count DESC
""")

duplicates = cursor.fetchall()

if duplicates:
    print(f"❌ Found {len(duplicates)} photos with duplicate analysis records:")
    print()
    total_duplicates = 0
    for row in duplicates[:10]:  # Show top 10
        photo_id = row['photo_id']
        count = row['count']
        total_duplicates += count - 1

        # Get photo path
        cursor.execute("SELECT file_path FROM photos WHERE id = ?", (photo_id,))
        photo = cursor.fetchone()
        photo_path = photo['file_path'] if photo else 'Unknown'

        print(f"Photo ID {photo_id}: {count} analysis records")
        print(f"  Path: {photo_path}")

        # Show dates of analysis
        cursor.execute("""
            SELECT analyzed_at FROM analysis_results 
            WHERE photo_id = ? 
            ORDER BY analyzed_at DESC
        """, (photo_id,))
        dates = cursor.fetchall()
        for i, date_row in enumerate(dates[:3], 1):
            print(f"  #{i}: {date_row['analyzed_at']}")
        if len(dates) > 3:
            print(f"  ... and {len(dates)-3} more")
        print()

    if len(duplicates) > 10:
        print(f"... and {len(duplicates)-10} more photos with duplicates")

    print(f"\n📊 Total duplicate records: {total_duplicates}")
    print(f"📊 Total analysis records: ", end="")
    cursor.execute("SELECT COUNT(*) FROM analysis_results")
    total = cursor.fetchone()[0]
    print(total)
    print(f"📊 Percentage duplicates: {total_duplicates/total*100:.1f}%")
else:
    print("✅ No duplicate analysis records found!")

conn.close()
