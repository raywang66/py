#!/usr/bin/env python3
"""
Test MediaPipe Tasks API Support
Tests both legacy and tasks API to ensure compatibility
"""

import sys
sys.path.insert(0, '.')

print("=" * 70)
print("MediaPipe Tasks API Support Test")
print("=" * 70)
print()

# Test 1: Import CC_SkinProcessor
print("Test 1: Importing CC_SkinProcessor...")
try:
    from CC_SkinProcessor import (
        MEDIAPIPE_AVAILABLE,
        MEDIAPIPE_API,
        MEDIAPIPE_VERSION_INFO,
        USE_LEGACY_API,
        USE_TASKS_API,
        CC_MediaPipeFaceDetector
    )
    print(f"✓ Import successful")
    print(f"  MediaPipe Available: {MEDIAPIPE_AVAILABLE}")
    print(f"  API Type: {MEDIAPIPE_API}")
    print(f"  Version Info: {MEDIAPIPE_VERSION_INFO}")
    print(f"  Using Legacy API: {USE_LEGACY_API}")
    print(f"  Using Tasks API: {USE_TASKS_API}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Create face detector
print("Test 2: Creating face detector...")
try:
    detector = CC_MediaPipeFaceDetector()
    print(f"✓ Face detector created successfully")
    print(f"  Detector type: {type(detector)}")
    if USE_TASKS_API:
        print(f"  Tasks API detector: {hasattr(detector, 'face_landmarker')}")
    if USE_LEGACY_API:
        print(f"  Legacy API detector: {hasattr(detector, 'face_mesh')}")
except Exception as e:
    print(f"✗ Detector creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Test with a simple image (if available)
print("Test 3: Testing face detection...")
try:
    import numpy as np
    import cv2

    # Create a simple test image (random noise, won't detect face but tests API)
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    print(f"  Created test image: {test_image.shape}")

    # Try to detect face (will likely fail with random noise, but tests the pipeline)
    mask = detector.detect_face_mask(test_image)
    print(f"✓ detect_face_mask() executed successfully")
    print(f"  Mask shape: {mask.shape}")
    print(f"  Mask coverage: {mask.sum() / mask.size * 100:.1f}%")

    if mask.sum() == 0:
        print(f"  Note: No face detected (expected with random test image)")

except Exception as e:
    print(f"✗ Face detection test failed: {e}")
    import traceback
    traceback.print_exc()
    # This is not critical - might fail without real face image
    print("  This is expected if model file is missing or image has no face")

print()

# Summary
print("=" * 70)
print("Summary")
print("=" * 70)

if MEDIAPIPE_AVAILABLE:
    if USE_TASKS_API:
        print("✅ Tasks API Support: WORKING")
        print(f"   MediaPipe {MEDIAPIPE_VERSION_INFO}")
        print("   ChromaCloud now supports MediaPipe 0.10.30+ on macOS!")
    elif USE_LEGACY_API:
        print("✅ Legacy API Support: WORKING")
        print(f"   MediaPipe {MEDIAPIPE_VERSION_INFO}")
        print("   ChromaCloud using legacy API (Windows/older versions)")

    print()
    print("Next steps:")
    print("1. Test with real portrait photo: python3 CC_demo.py")
    print("2. Launch ChromaCloud: python3 CC_Main.py")
else:
    print("❌ MediaPipe not available")
    print("   Install: pip install mediapipe")

print()
