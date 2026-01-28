"""
ChromaCloud - MediaPipe Face Detection Test
Test the new MediaPipe-based skin detection on your photos
"""

import sys
from pathlib import Path

print("=" * 70)
print("ChromaCloud - MediaPipe Face Detection Test")
print("=" * 70)
print()

# Check MediaPipe installation
try:
    import mediapipe as mp
    print("✓ MediaPipe installed")
    print(f"  Version: {mp.__version__}")
except ImportError:
    print("✗ MediaPipe not installed!")
    print("  Install with: pip install mediapipe")
    sys.exit(1)

# Test CC_SkinProcessor
try:
    from CC_SkinProcessor import CC_SkinProcessor
    import numpy as np
    from PIL import Image
    import cv2

    print("✓ CC_SkinProcessor loaded")
    print()

    # Initialize processor
    print("Initializing MediaPipe Face Mesh...")
    processor = CC_SkinProcessor(use_mediapipe=True)
    print("✓ Processor initialized")
    print()

    # Look for test photos
    photos_dir = Path(__file__).parent / "Photos"

    if photos_dir.exists():
        test_images = list(photos_dir.glob("*.JPG")) + \
                      list(photos_dir.glob("*.jpg")) + \
                      list(photos_dir.glob("*.png"))

        if test_images:
            test_image = test_images[0]
            print(f"Processing: {test_image.name}")
            print("-" * 70)

            # Process image
            import time
            start = time.time()
            point_cloud, mask = processor.process_image(test_image, return_mask=True)
            elapsed = (time.time() - start) * 1000

            print(f"✓ Processing complete in {elapsed:.1f} ms")
            print()

            if len(point_cloud) > 0:
                print("Results:")
                print(f"  • Skin pixels: {len(point_cloud):,}")
                print(f"  • Mask coverage: {mask.sum() / mask.size * 100:.2f}%")
                print(f"  • Hue range: {point_cloud[:, 0].min():.1f}° - {point_cloud[:, 0].max():.1f}°")
                print(f"  • Saturation avg: {point_cloud[:, 1].mean() * 100:.1f}%")
                print(f"  • Lightness avg: {point_cloud[:, 2].mean() * 100:.1f}%")
                print()

                # Save visualization
                output_dir = Path(__file__).parent / "output"
                output_dir.mkdir(exist_ok=True)

                # Load original image
                img = cv2.imread(str(test_image))
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Create visualization
                overlay = img_rgb.copy()
                overlay[mask == 1] = overlay[mask == 1] * 0.5 + np.array([255, 100, 100]) * 0.5

                # Save
                output_path = output_dir / f"mediapipe_test_{test_image.stem}.png"
                Image.fromarray(overlay.astype(np.uint8)).save(output_path)
                print(f"✓ Visualization saved: {output_path}")
                print()

                # Show statistics by region
                h, s, l = point_cloud[:, 0], point_cloud[:, 1], point_cloud[:, 2]

                print("Skin Tone Distribution:")
                print(f"  • Shadows (L<30%): {np.sum(l < 0.3) / len(l) * 100:.1f}%")
                print(f"  • Midtones (30-70%): {np.sum((l >= 0.3) & (l <= 0.7)) / len(l) * 100:.1f}%")
                print(f"  • Highlights (L>70%): {np.sum(l > 0.7) / len(l) * 100:.1f}%")

            else:
                print("⚠ No skin pixels detected")
                print("  • Make sure the image contains a clear face")
                print("  • Try a frontal portrait with good lighting")

        else:
            print("⚠ No test images found in Photos/ directory")
            print(f"  • Add JPG/PNG files to: {photos_dir}")
    else:
        print(f"⚠ Photos directory not found: {photos_dir}")
        print("  • Create the directory and add test images")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("Test complete!")
print()
print("Next steps:")
print("  1. Run full demo: python CC_demo.py")
print("  2. Launch GUI: python CC_MainApp.py")
print("=" * 70)

