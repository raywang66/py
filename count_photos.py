from pathlib import Path

photos_dir = Path(__file__).parent / "Photos"
extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG', '*.arw', '*.nef', '*.cr2', '*.cr3', '*.dng']

photos = []
for ext in extensions:
    photos.extend(photos_dir.glob(ext))

print(f"Total photos found in root directory: {len(photos)}")
print(f"\nFirst 10 photos:")
for i, photo in enumerate(sorted(photos)[:10]):
    print(f"  {i+1}. {photo.name}")
