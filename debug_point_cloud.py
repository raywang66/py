"""
Debug script to check if point_cloud_data exists in the database
"""
import sqlite3
from pathlib import Path

db_path = Path("chromacloud.db")

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check analysis_results table
cursor.execute("""
    SELECT 
        photo_id,
        face_detected,
        num_points,
        LENGTH(point_cloud_data) as point_cloud_size,
        analyzed_at
    FROM analysis_results
    ORDER BY analyzed_at DESC
    LIMIT 10
""")

print("=" * 80)
print("Recent Analysis Results:")
print("=" * 80)

rows = cursor.fetchall()
if not rows:
    print("❌ No analysis results found in database!")
else:
    for row in rows:
        print(f"\nPhoto ID: {row['photo_id']}")
        print(f"  Face Detected: {bool(row['face_detected'])}")
        print(f"  Num Points: {row['num_points']}")
        print(f"  Point Cloud Data Size: {row['point_cloud_size']} bytes")
        print(f"  Analyzed At: {row['analyzed_at']}")

        if row['point_cloud_size'] == 0 or row['point_cloud_size'] is None:
            print(f"  ⚠️  WARNING: No point_cloud_data!")

# Check photos table
cursor.execute("""
    SELECT COUNT(*) as total FROM photos
""")
photo_count = cursor.fetchone()['total']
print(f"\n{'=' * 80}")
print(f"Total photos in database: {photo_count}")

# Check analyzed photos
cursor.execute("""
    SELECT COUNT(*) as analyzed FROM analysis_results WHERE face_detected = 1
""")
analyzed_count = cursor.fetchone()['analyzed']
print(f"Photos with face detected: {analyzed_count}")

cursor.execute("""
    SELECT COUNT(*) as with_cloud 
    FROM analysis_results 
    WHERE face_detected = 1 AND point_cloud_data IS NOT NULL AND LENGTH(point_cloud_data) > 0
""")
with_cloud = cursor.fetchone()['with_cloud']
print(f"Photos with point_cloud_data: {with_cloud}")

if analyzed_count > 0 and with_cloud < analyzed_count:
    print(f"\n⚠️  WARNING: {analyzed_count - with_cloud} photos have face_detected=1 but NO point_cloud_data!")
    print("This is why Visualize button is not enabled!")

conn.close()
print(f"\n{'=' * 80}")
