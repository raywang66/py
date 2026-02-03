"""
验证所有 Hue 修复是否正确
"""
import sqlite3
from pathlib import Path

db_path = Path("chromacloud.db")

if not db_path.exists():
    print("❌ 数据库不存在，请先运行 CC_Main.py 并分析一些照片")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*70)
print("验证 AutoAnalyzer Hue 修复")
print("="*70)

# 检查分析结果
cursor.execute("""
    SELECT 
        p.file_name,
        ar.hue_mean,
        ar.hue_std,
        ar.saturation_mean,
        ar.lightness_mean,
        ar.hue_very_red,
        ar.hue_red_orange,
        ar.hue_normal,
        ar.hue_yellow,
        ar.hue_very_yellow,
        ar.hue_abnormal
    FROM analysis_results ar
    JOIN photos p ON ar.photo_id = p.id
    WHERE ar.face_detected = 1
    ORDER BY ar.analyzed_at DESC
    LIMIT 5
""")

results = cursor.fetchall()

if not results:
    print("\n❌ 数据库中没有分析结果")
    print("   请运行 CC_Main.py 并使用 AutoAnalyzer 或 Analyze 按钮分析照片")
    conn.close()
    exit(1)

print(f"\n找到 {len(results)} 条分析结果\n")

all_correct = True

for i, row in enumerate(results, 1):
    file_name, h_mean, h_std, s_mean, l_mean, very_red, red_orange, normal, yellow, very_yellow, abnormal = row

    print(f"{i}. {file_name}")
    print(f"   Hue:        {h_mean:.2f}° ± {h_std:.2f}°")
    print(f"   Saturation: {s_mean * 100:.1f}%")
    print(f"   Lightness:  {l_mean * 100:.1f}%")
    print(f"   Hue Distribution:")
    print(f"     Very Red:    {very_red * 100:.1f}%")
    print(f"     Red-Orange:  {red_orange * 100:.1f}%")
    print(f"     Normal:      {normal * 100:.1f}%")
    print(f"     Yellow:      {yellow * 100:.1f}%")
    print(f"     Very Yellow: {very_yellow * 100:.1f}%")
    print(f"     Abnormal:    {abnormal * 100:.1f}%")

    # 验证 Hue 是否在正确范围
    if h_mean < 0 or h_mean > 360:
        print(f"   ❌ ERROR: Hue {h_mean:.2f}° 超出范围 [0, 360]")
        all_correct = False
    elif h_mean > 60:
        print(f"   ⚠️  WARNING: Hue {h_mean:.2f}° > 60°，可能不是正常肤色")
        print(f"      (正常肤色应该在 [0, 60] 范围内)")
    else:
        print(f"   ✅ Hue 在正常范围 [0, 60]")

    # 验证分布总和是否接近 100%
    total_dist = (very_red + red_orange + normal + yellow + very_yellow + abnormal) * 100
    if abs(total_dist - 100) > 1:
        print(f"   ⚠️  WARNING: 分布总和 {total_dist:.1f}% 不等于 100%")

    print()

conn.close()

print("="*70)
print("总结")
print("="*70)

if all_correct:
    print("✅ 所有 Hue 值都在正确范围内！")
    print("\n如果所有值都在 [0, 60] 范围，说明修复成功：")
    print("  1. AutoAnalyzer 计算时不再错误地 * 360")
    print("  2. 数据库存储的是正确的度数")
    print("  3. 显示时也不再错误地 * 360")
else:
    print("❌ 发现错误的 Hue 值！")
    print("\n可能的原因：")
    print("  1. 这些是旧数据（修复前分析的）")
    print("  2. 代码还没有正确更新")
    print("\n解决方法：")
    print("  1. 删除 chromacloud.db")
    print("  2. 重新运行 CC_Main.py")
    print("  3. 重新分析照片")

print("\n" + "="*70)
