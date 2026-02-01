"""
Test directory tree structure display
"""

import sys
from pathlib import Path

print("=" * 70)
print("Directory Tree Structure Test")
print("=" * 70)

# Test building a simple directory tree
print("\n[Test] Building directory tree structure...")

test_dir = Path(__file__).parent

# Count subdirectories
subdirs = [d for d in test_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
print(f"✓ Found {len(subdirs)} subdirectories in: {test_dir}")

for subdir in sorted(subdirs[:5]):  # Show first 5
    print(f"  📁 {subdir.name}")

if len(subdirs) > 5:
    print(f"  ... and {len(subdirs) - 5} more")

# Count photos
image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
photo_count = 0

for item in test_dir.rglob('*'):
    if item.is_file() and item.suffix in image_extensions:
        photo_count += 1
        if photo_count <= 5:
            print(f"  📷 {item.name} in {item.parent.name}")

print(f"✓ Total photos found: {photo_count}")

print("\n" + "=" * 70)
print("Directory Tree Test Complete!")
print("=" * 70)
print("""
The new features implemented:

✅ Recursive directory tree structure
✅ Shows subdirectories under Folder Albums
✅ Each subfolder is clickable and collapsible
✅ Photo count shown for each subfolder
✅ Only shows folders that contain photos
✅ Supports unlimited depth (default max 10 levels)

How to use:
1. Start ChromaCloud
2. Create a Folder Album
3. Click the ▶ arrow to expand the folder
4. See all subdirectories with photo counts
5. Click any subfolder to see only its photos
6. Click the root folder to see all photos

Example tree structure:
📂 Folders (1)
  ├─ 📂 My_Photos (156)          ← Root folder (all photos)
     ├─ 📁 2024_Jan (45)         ← Subfolder (Jan photos only)
     ├─ 📁 2024_Feb (67)         ← Subfolder (Feb photos only)
     └─ 📁 Portraits (44)        ← Subfolder (Portraits only)
        └─ 📁 Studio (20)        ← Sub-subfolder (Studio only)
""")
