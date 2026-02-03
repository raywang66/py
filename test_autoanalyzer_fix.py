"""
Test script to verify AutoAnalyzer thread safety fix
"""
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))

from CC_SkinProcessor import CC_SkinProcessor
from CC_AutoAnalyzer import CC_AutoAnalyzer
from PySide6.QtCore import QCoreApplication

print("="*70)
print("TESTING AUTOANALYZER THREAD SAFETY FIX")
print("="*70)

# Find a test image
photos_dir = Path(__file__).parent / "Photos"
test_images = list(photos_dir.glob("*.JPG")) + list(photos_dir.glob("*.jpg"))

if not test_images:
    print("❌ No test images found in Photos folder")
    sys.exit(1)

test_image = test_images[0]
print(f"\nTest image: {test_image.name}")
print("-"*70)

# Create QApplication for signal/slot
app = QCoreApplication(sys.argv)

# Test 1: Main thread processor
print("\n1️⃣  Testing MAIN THREAD (Analyze Button simulation)")
print("-"*70)
processor_main = CC_SkinProcessor()
image_rgb = processor_main._load_image(test_image)
point_cloud_main, mask_main = processor_main.process_image(image_rgb, return_mask=True)

print(f"✓ Main thread results:")
print(f"   Skin pixels: {len(point_cloud_main)}")
print(f"   Mask coverage: {mask_main.sum() / mask_main.size * 100:.2f}%")
if len(point_cloud_main) > 0:
    print(f"   Hue mean: {point_cloud_main[:, 0].mean():.4f}")
    print(f"   Saturation mean: {point_cloud_main[:, 1].mean():.4f}")

# Test 2: AutoAnalyzer (new thread)
print("\n2️⃣  Testing AUTO ANALYZER (Background Thread)")
print("-"*70)

db_path = Path(__file__).parent / "chromacloud.db"
analyzer = CC_AutoAnalyzer(None, db_path)  # processor=None (will create its own)

# Add test photo
analyzer.add_photo(test_image, album_id=1)

results_received = []

def on_complete(photo_id, results):
    print(f"✓ AutoAnalyzer results received:")
    print(f"   Photo ID: {photo_id}")
    print(f"   Face detected: {results.get('face_detected')}")
    print(f"   Skin pixels: {results.get('num_points')}")
    print(f"   Mask coverage: {results.get('mask_coverage', 0) * 100:.2f}%")
    print(f"   Hue mean: {results.get('hue_mean'):.4f}")
    print(f"   Saturation mean: {results.get('saturation_mean'):.4f}")
    results_received.append(results)
    app.quit()

def on_failed(photo_id, error):
    print(f"❌ AutoAnalyzer failed: {error}")
    app.quit()

analyzer.analysis_complete.connect(on_complete)
analyzer.analysis_failed.connect(on_failed)

# Start analyzer
analyzer.start()
print("⏳ Waiting for AutoAnalyzer to process...")

# Run event loop
app.exec()

# Stop analyzer
analyzer.stop()
analyzer.wait()

# Compare results
print("\n" + "="*70)
print("📊 COMPARISON")
print("="*70)

if results_received:
    auto_result = results_received[0]

    main_hue = point_cloud_main[:, 0].mean() if len(point_cloud_main) > 0 else 0
    auto_hue = auto_result.get('hue_mean', 0)

    main_sat = point_cloud_main[:, 1].mean() if len(point_cloud_main) > 0 else 0
    auto_sat = auto_result.get('saturation_mean', 0)

    hue_diff = abs(main_hue - auto_hue)
    sat_diff = abs(main_sat - auto_sat)

    print(f"Main thread     - Hue: {main_hue:.4f}, Saturation: {main_sat:.4f}")
    print(f"AutoAnalyzer    - Hue: {auto_hue:.4f}, Saturation: {auto_sat:.4f}")
    print(f"Difference      - Hue: {hue_diff:.4f}, Saturation: {sat_diff:.4f}")

    if hue_diff < 0.001 and sat_diff < 0.001:
        print("\n✅ SUCCESS: Results are identical!")
        print("   Face detection works correctly in both threads")
    else:
        print(f"\n⚠️  WARNING: Results differ!")
        print(f"   Hue difference: {hue_diff:.4f}")
        print(f"   Saturation difference: {sat_diff:.4f}")
else:
    print("❌ No results received from AutoAnalyzer")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
