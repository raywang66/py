import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "chromacloud.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN sat_very_low > 0 OR sat_low > 0 OR sat_normal > 0 OR sat_high > 0 OR sat_very_high > 0 THEN 1 ELSE 0 END) as has_data
    FROM analysis_results
""")
row = cursor.fetchone()
print(f"Total: {row[0]}, With saturation data: {row[1]}")
conn.close()
