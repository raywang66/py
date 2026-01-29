"""
Quick script to add saturation columns to database
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "chromacloud.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

sat_columns = [
    'sat_very_low',
    'sat_low',
    'sat_normal',
    'sat_high',
    'sat_very_high'
]

print("Adding saturation columns...")
for col in sat_columns:
    try:
        cursor.execute(f"ALTER TABLE analysis_results ADD COLUMN {col} REAL DEFAULT 0.0")
        print(f"✅ Added: {col}")
    except sqlite3.OperationalError as e:
        print(f"⚠️  {col}: {e}")

conn.commit()

# Verify
cursor.execute("PRAGMA table_info(analysis_results)")
columns = [row[1] for row in cursor.fetchall()]
print(f"\nTotal columns: {len(columns)}")
print(f"Saturation columns present: {sum(1 for c in columns if c.startswith('sat_'))}")

conn.close()
print("\n✅ Done!")
