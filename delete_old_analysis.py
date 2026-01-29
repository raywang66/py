"""
Delete all old analysis results so you can re-analyze everything with saturation data
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "chromacloud.db"

print("=" * 60)
print("Delete Old Analysis Results")
print("=" * 60)
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Count before
cursor.execute("SELECT COUNT(*) FROM analysis_results")
before = cursor.fetchone()[0]
print(f"Analysis results before: {before}")

# Delete all
cursor.execute("DELETE FROM analysis_results")
conn.commit()

# Count after
cursor.execute("SELECT COUNT(*) FROM analysis_results")
after = cursor.fetchone()[0]
print(f"Analysis results after: {after}")
print()
print(f"Deleted: {before - after} records")

conn.close()

print()
print("=" * 60)
print("Done! Now re-analyze all photos to generate saturation data.")
print("=" * 60)
