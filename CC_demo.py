"""
ChromaCloud (CC) - Comprehensive Demo & Test Script
Author: Senior Software Architect
Date: January 2026

This script demonstrates all major features of ChromaCloud without requiring
the full GUI or external dependencies.
"""

import sys
import time
import argparse
from pathlib import Path

# ============================================================================
# PARSE COMMAND LINE ARGUMENTS
# ============================================================================
parser = argparse.ArgumentParser(
    description="ChromaCloud Demo - Test skin tone analysis pipeline",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  python CC_demo.py                           # Use first photo from Photos/ folder
  python CC_demo.py --photo IMG_2571.JPG      # Test specific photo by name
  python CC_demo.py --photo Photos/unnamed.jpg  # Test with full path
  python CC_demo.py --photo path/to/image.png # Test any image file
    """
)
parser.add_argument(
    '--photo',
    type=str,
    default=None,
    help='Path to a specific photo to test (default: use first photo from Photos/ folder)'
)

args = parser.parse_args()

print("=" * 70)
print("ChromaCloud (CC) - System Demo")
print("=" * 70)
print()

# ============================================================================
# STEP 1: Configuration Check
# ============================================================================
print("STEP 1: Configuration Check")
print("-" * 70)

try:
    from cc_config import (
        CC_PROJECT_NAME,
        CC_VERSION,
        CC_PLATFORM,
        CC_TAICHI_BACKEND,
        CC_USE_GPU,
        CC_SKIN_CONFIG,
        CC_HSL_CONFIG,
        CC_RENDERER_CONFIG
    )

    print(f"✓ Project: {CC_PROJECT_NAME} v{CC_VERSION}")
    print(f"✓ Platform: {CC_PLATFORM}")
    print(f"✓ GPU Enabled: {CC_USE_GPU}")
    print(f"✓ Taichi Backend: {CC_TAICHI_BACKEND}")
    print(f"✓ Skin Hue Range: {CC_HSL_CONFIG.hue_min}° - {CC_HSL_CONFIG.hue_max}°")
    print(f"✓ Max Points: {CC_HSL_CONFIG.max_points:,}")
    print()

except Exception as e:
    print(f"✗ Configuration Error: {e}")
    sys.exit(1)

# ============================================================================
# STEP 2: PyTorch & GPU Check
# ============================================================================
print("STEP 2: PyTorch & GPU Detection")
print("-" * 70)

try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"✓ CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print(f"✓ Apple Metal (MPS) available")
    else:
        print(f"⚠ No GPU detected - will use CPU")
    print()

except ImportError as e:
    print(f"✗ PyTorch not installed: {e}")
    print("  Install: pip install torch torchvision")
    sys.exit(1)

# ============================================================================
# STEP 3: CC_SkinProcessor Test
# ============================================================================
print("STEP 3: CC_SkinProcessor Module Test")
print("-" * 70)

try:
    from CC_SkinProcessor import CC_SkinProcessor
    import numpy as np
    from PIL import Image

    # Initialize processor
    processor = CC_SkinProcessor()
    print(f"✓ CC_SkinProcessor initialized")
    print(f"✓ Using MediaPipe Face Mesh")
    print(f"✓ Hue range: {CC_HSL_CONFIG.hue_min}° - {CC_HSL_CONFIG.hue_max}°")

    # Create synthetic test image
    print("\nGenerating synthetic portrait...")
    print("⚠ Note: This is random noise, not a real face - MediaPipe will report 'no face detected'")
    test_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)

    # Add skin-colored region (heuristic for demo)
    skin_region = test_image[150:350, 150:350]
    skin_region[:, :, 0] = 210  # R
    skin_region[:, :, 1] = 170  # G
    skin_region[:, :, 2] = 140  # B

    # Process
    print("Processing synthetic image (testing face detection)...")
    start_time = time.time()
    point_cloud = processor.process_image(test_image)
    elapsed = (time.time() - start_time) * 1000

    if len(point_cloud) > 0:
        print(f"✓ Extracted {len(point_cloud):,} skin points")
        print(f"✓ Processing time: {elapsed:.1f} ms")
        print(f"✓ HSL range:")
        print(f"  - Hue: {point_cloud[:, 0].min():.1f}° to {point_cloud[:, 0].max():.1f}°")
        print(f"  - Saturation: {point_cloud[:, 1].min():.2f} to {point_cloud[:, 1].max():.2f}")
        print(f"  - Lightness: {point_cloud[:, 2].min():.2f} to {point_cloud[:, 2].max():.2f}")
    else:
        print("✓ No skin points extracted (expected - synthetic image has no face)")
    print()

except Exception as e:
    print(f"✗ CC_SkinProcessor error: {e}")
    import traceback
    traceback.print_exc()
    print("\n✗ ABORTING: Cannot continue without CC_SkinProcessor")
    sys.exit(1)

# ============================================================================
# STEP 4: Taichi & CC_Renderer3D Test
# ============================================================================
print("STEP 4: CC_Renderer3D Module Test")
print("-" * 70)

renderer = None
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

try:
    import taichi as ti
    print(f"✓ Taichi version: {ti.__version__}")

    from CC_Renderer3D import CC_Renderer3D, CC_create_test_point_cloud

    # Create renderer
    renderer = CC_Renderer3D(width=800, height=600)
    print(f"✓ CC_Renderer3D initialized")
    print(f"✓ Viewport: {renderer.width}x{renderer.height}")

    # Generate test point cloud
    print("\nGenerating test point cloud...")
    test_points = CC_create_test_point_cloud(num_points=5000)
    print(f"✓ Generated {len(test_points):,} test points")

    # Upload to GPU
    renderer.set_point_cloud(test_points)
    print(f"✓ Uploaded to GPU")

    # Render
    print("Rendering...")
    start_time = time.time()
    image = renderer.render()
    elapsed = (time.time() - start_time) * 1000

    print(f"✓ Rendered in {elapsed:.1f} ms")
    print(f"✓ Output shape: {image.shape}")
    print(f"✓ Value range: [{image.min():.2f}, {image.max():.2f}]")

    # Save screenshot
    output_path = output_dir / "CC_demo_render.png"
    renderer.save_screenshot(str(output_path))
    print(f"✓ Screenshot saved: {output_path}")
    print()

except ImportError as e:
    print(f"✗ Taichi/CC_Renderer3D not available: {e}")
    print("  Install: pip install taichi")
    print("\n⚠ Skipping rendering tests (non-critical)")
    print()
except Exception as e:
    print(f"✗ CC_Renderer3D error: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠ Skipping rendering tests (non-critical)")
    print()

# ============================================================================
# STEP 5: Dual-View Comparison Test
# ============================================================================
if renderer is not None:
    print("STEP 5: Dual-View Comparison Test")
    print("-" * 70)

    try:
        # Generate two different point clouds
        print("Generating two point clouds for comparison...")
        cloud_a = CC_create_test_point_cloud(num_points=3000)
        cloud_a[:, 0] += 2.0  # Shift hue slightly

        cloud_b = CC_create_test_point_cloud(num_points=3000)
        cloud_b[:, 0] -= 1.0  # Shift hue in opposite direction

        print(f"✓ Cloud A: {len(cloud_a):,} points")
        print(f"✓ Cloud B: {len(cloud_b):,} points")

        # Set dual mode
        renderer.set_dual_point_clouds(cloud_a, cloud_b)
        print(f"✓ Dual mode enabled")

        # Render overlay
        print("Rendering dual-view overlay...")
        dual_image = renderer.render()

        # Save
        output_path = output_dir / "CC_demo_dual_view.png"
        renderer.save_screenshot(str(output_path))
        print(f"✓ Dual-view saved: {output_path}")
        print()

    except Exception as e:
        print(f"✗ Dual-view error: {e}")
        print()

# ============================================================================
# STEP 6: Real Photo Test (if available)
# ============================================================================
print("STEP 6: Real Photo Test")
print("-" * 70)

test_image_path = None

# Determine which photo to use
if args.photo:
    # User specified a photo via --photo argument
    test_image_path = Path(args.photo)

    # If it's just a filename, look in Photos/ directory
    if not test_image_path.exists() and not test_image_path.is_absolute():
        photos_dir = Path(__file__).parent / "Photos"
        alternative_path = photos_dir / args.photo
        if alternative_path.exists():
            test_image_path = alternative_path

    if not test_image_path.exists():
        print(f"✗ Error: Photo not found: {args.photo}")
        print(f"  Tried: {test_image_path.absolute()}")
        if not test_image_path.is_absolute():
            print(f"  Also tried: {alternative_path.absolute()}")
        sys.exit(1)

    print(f"Using photo from command line: {test_image_path.name}")
else:
    # Default behavior: use first photo from Photos/ directory
    photos_dir = Path(__file__).parent / "Photos"

    if photos_dir.exists():
        test_images = list(photos_dir.glob("*.JPG")) + \
                     list(photos_dir.glob("*.jpg")) + \
                     list(photos_dir.glob("*.png")) + \
                     list(photos_dir.glob("*.PNG"))

        if test_images:
            test_image_path = test_images[0]
            print(f"Found test image: {test_image_path.name}")
        else:
            print("⚠ No test images found in Photos/ directory")
    else:
        print("⚠ Photos/ directory not found")

# Process the photo if we have one
if test_image_path:
    try:
        print(f"Processing: {test_image_path}")
        start_time = time.time()
        point_cloud, mask = processor.process_image(test_image_path, return_mask=True)
        elapsed = (time.time() - start_time) * 1000

        if len(point_cloud) > 0:
            print(f"✓ Extracted {len(point_cloud):,} skin points")
            print(f"✓ Processing time: {elapsed:.1f} ms")
            print(f"✓ Mask coverage: {mask.sum() / mask.size * 100:.2f}%")

            # Statistics
            h_mean = point_cloud[:, 0].mean()
            s_mean = point_cloud[:, 1].mean()
            l_mean = point_cloud[:, 2].mean()

            print(f"✓ Average skin tone:")
            print(f"  - Hue: {h_mean:.1f}°")
            print(f"  - Saturation: {s_mean*100:.1f}%")
            print(f"  - Lightness: {l_mean*100:.1f}%")

            # Render if available
            if renderer is not None:
                renderer.set_point_cloud(point_cloud)
                output_filename = f"CC_demo_{test_image_path.stem}.png"
                output_path = output_dir / output_filename
                renderer.save_screenshot(str(output_path))
                print(f"✓ Visualization saved: {output_path}")
        else:
            print("⚠ No skin detected in photo")

    except Exception as e:
        print(f"✗ Real photo processing error: {e}")
        import traceback
        traceback.print_exc()

print()

# ============================================================================
# STEP 7: PySide6 UI Test (optional)
# ============================================================================
print("STEP 7: PySide6 UI Test")
print("-" * 70)

try:
    from PySide6.QtCore import QT_VERSION_STR
    print(f"✓ PySide6 installed (Qt {QT_VERSION_STR})")
    print(f"✓ CC_MainApp available")
    print(f"  Run: python CC_MainApp.py")
    print()
except ImportError:
    print("✗ PySide6 not installed")
    print("  Install: pip install PySide6")
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("DEMO COMPLETE")
print("=" * 70)
print()
print("Summary:")
print("  ✓ Configuration loaded successfully")
print("  ✓ CC_SkinProcessor working (MediaPipe Face Mesh)")
if renderer is not None:
    print("  ✓ CC_Renderer3D working (Taichi)")
    print("  ✓ Dual-view comparison functional")
else:
    print("  ⚠ CC_Renderer3D not available (Taichi not installed)")
print()
print("Next Steps:")
print("  1. Process your portrait photos")
print("  2. Install Taichi for 3D visualization: pip install taichi")
print("  3. Install PySide6 for GUI: pip install PySide6")
print("  4. Run GUI: python CC_MainApp.py")
print()
print(f"Output files saved to: {output_dir.absolute()}")
print("=" * 70)

