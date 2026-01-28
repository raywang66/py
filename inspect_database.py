"""
Inspect database to see what data is actually stored
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "chromacloud.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check analysis_results structure
cursor.execute("PRAGMA table_info(analysis_results)")
columns = cursor.fetchall()
print("=== analysis_results columns ===")
for col in columns:
    print(f"  {col['name']}: {col['type']}")

# Check sample data
cursor.execute("""
    SELECT id, photo_id, lightness_low, lightness_mid, lightness_high, 
           typeof(lightness_low) as low_type,
           typeof(lightness_mid) as mid_type,
           typeof(lightness_high) as high_type
    FROM analysis_results 
    LIMIT 5
""")
rows = cursor.fetchall()
print("\n=== Sample data (first 5 records) ===")
for row in rows:
    print(f"ID {row['id']}: low={row['lightness_low']} ({row['low_type']}), "
          f"mid={row['lightness_mid']} ({row['mid_type']}), "
          f"high={row['lightness_high']} ({row['high_type']})")

# Count total records
cursor.execute("SELECT COUNT(*) as total FROM analysis_results")
total = cursor.fetchone()['total']
print(f"\n=== Total analysis records: {total} ===")

# Count records with non-null lightness data
cursor.execute("""
    SELECT COUNT(*) as count 
    FROM analysis_results 
    WHERE lightness_low IS NOT NULL 
      AND lightness_mid IS NOT NULL 
      AND lightness_high IS NOT NULL
""")
with_data = cursor.fetchone()['count']
print(f"Records with lightness data: {with_data}")
print(f"Records missing lightness data: {total - with_data}")

conn.close()
