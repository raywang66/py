import sqlite3
from pathlib import Path

output = []

# Check database
db_path = Path("C:/Users/rwang/lc_sln/py/chromacloud.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

output.append("DATABASE CONTENTS:")
output.append("=" * 60)

tables = ['albums', 'photos', 'album_photos', 'thumbnail_cache', 'folder_structure']
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        output.append(f"{table:25s}: {count:5d} rows")
    except Exception as e:
        output.append(f"{table:25s}: ERROR - {str(e)}")

conn.close()

# Check file system
output.append("\n" + "=" * 60)
output.append("FILE SYSTEM (Photos folder):")
output.append("=" * 60)

photos_dir = Path("C:/Users/rwang/lc_sln/py/Photos")
extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG', '*.arw']

photos = []
for ext in extensions:
    found = list(photos_dir.glob(ext))
    if found:
        output.append(f"{ext:10s}: {len(found):3d} files")
    photos.extend(found)

output.append(f"\nTOTAL: {len(photos)} photos in Photos root directory")

output.append("\n" + "=" * 60)
output.append("EXPLANATION:")
output.append("=" * 60)
output.append("""
当你点击 "All Photos" 时:
  → CC_Main._load_all_photos() 扫描 Photos 文件夹（文件系统）
  → 不查询数据库！
  
所以即使数据库是空的，只要 Photos 文件夹里有照片文件，
就会显示出来。这是正常的设计。

如果你想测试数据库是否真的是空的：
1. 创建一个新的 Album
2. 点击这个 Album  
3. 应该显示 0 张照片（因为还没添加照片到这个 Album）
""")

# Write to file
with open("C:/Users/rwang/lc_sln/py/photo_count_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Report written to: photo_count_report.txt")
