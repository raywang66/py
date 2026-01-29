"""
Check if saturation data was actually saved to database
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "chromacloud.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Checking latest analysis results...")
print("=" * 60)

# Get the 5 most recent analysis results
cursor.execute("""
    SELECT 
        p.file_name,
        ar.analyzed_at,
        ar.sat_very_low,
        ar.sat_low,
        ar.sat_normal,
        ar.sat_high,
        ar.sat_very_high
    FROM analysis_results ar
    JOIN photos p ON ar.photo_id = p.id
    ORDER BY ar.analyzed_at DESC
    LIMIT 5
""")

print("\nLatest 5 analysis results:")
for i, row in enumerate(cursor.fetchall(), 1):
    fname, analyzed_at, vl, l, n, h, vh = row
    total = (vl or 0) + (l or 0) + (n or 0) + (h or 0) + (vh or 0)
    print(f"\n{i}. {fname[:50]}")
    print(f"   Analyzed: {analyzed_at}")
    print(f"   Saturation: vl={vl:.1f}, l={l:.1f}, n={n:.1f}, h={h:.1f}, vh={vh:.1f}")
    print(f"   Total: {total:.1f}%")
    if total > 0:
        print("   ✅ HAS saturation data")
    else:
        print("   ❌ NO saturation data (all zeros)")

# Count how many have saturation data
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN sat_very_low > 0 OR sat_low > 0 OR sat_normal > 0 OR sat_high > 0 OR sat_very_high > 0 THEN 1 ELSE 0 END) as has_sat
    FROM analysis_results
""")
total, has_sat = cursor.fetchone()

print("\n" + "=" * 60)
print(f"\nSummary:")
print(f"  Total analysis results: {total}")
print(f"  With saturation data: {has_sat}")
print(f"  Without saturation data: {total - has_sat}")

conn.close()
