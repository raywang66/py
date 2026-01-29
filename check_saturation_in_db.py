"""
Check database for saturation distribution data
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "chromacloud.db"

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

print("Checking database for saturation distribution data...")
print("=" * 60)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check table structure
print("\n1️⃣ Checking table columns...")
cursor.execute("PRAGMA table_info(analysis_results)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Total columns: {len(columns)}")

sat_columns = [c for c in columns if c.startswith('sat_')]
print(f"Saturation columns: {sat_columns}")

if len(sat_columns) == 5:
    print("✅ All 5 saturation columns exist")
else:
    print(f"❌ Missing saturation columns! Only found {len(sat_columns)}")

# Check if there's any data
print("\n2️⃣ Checking saturation data...")
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN sat_very_low > 0 OR sat_low > 0 OR sat_normal > 0 OR sat_high > 0 OR sat_very_high > 0 THEN 1 ELSE 0 END) as has_data
    FROM analysis_results
""")
row = cursor.fetchone()
total = row[0]
has_data = row[1]

print(f"Total analyzed photos: {total}")
print(f"Photos with saturation data: {has_data}")
print(f"Photos without saturation data: {total - has_data}")

if has_data > 0:
    print("✅ Some photos have saturation data")
else:
    print("❌ NO photos have saturation data")

# Show sample data
print("\n3️⃣ Sample saturation data (first 5 photos)...")
cursor.execute("""
    SELECT 
        p.file_name,
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

for i, row in enumerate(cursor.fetchall(), 1):
    fname, vl, l, n, h, vh = row
    total_sat = (vl or 0) + (l or 0) + (n or 0) + (h or 0) + (vh or 0)
    print(f"\n{i}. {fname[:40]}")
    print(f"   VeryLow: {vl:.1f}%, Low: {l:.1f}%, Normal: {n:.1f}%")
    print(f"   High: {h:.1f}%, VeryHigh: {vh:.1f}%")
    print(f"   Total: {total_sat:.1f}%")

    if total_sat > 0:
        print("   ✅ Has saturation data")
    else:
        print("   ❌ No saturation data (all zeros)")

conn.close()

print("\n" + "=" * 60)
print("\n💡 Summary:")
print(f"   Database has {total} analyzed photos")
print(f"   {has_data} photos have saturation data")
print(f"   {total - has_data} photos need re-analysis")

if has_data == 0:
    print("\n⚠️  NO saturation data found!")
    print("   Please run 'Batch Analyze' again to generate data.")
else:
    print("\n✅ Database contains saturation data!")
    print("   Check if Statistics Window can read this data.")
