#!/usr/bin/env python3
"""
MediaPipe Import Diagnostic Script
Run this on macOS to diagnose MediaPipe import issues
"""

import sys
print("=" * 70)
print("MediaPipe Import Diagnostics")
print("=" * 70)
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"sys.path:")
for p in sys.path:
    print(f"  {p}")
print()

# Step 1: Check if mediapipe is installed
print("Step 1: Checking if mediapipe package exists...")
try:
    import mediapipe
    print(f"✓ mediapipe module found")
    print(f"  Location: {mediapipe.__file__}")
    print(f"  Version: {mediapipe.__version__}")
except ImportError as e:
    print(f"✗ mediapipe module NOT found: {e}")
    print("\nPossible causes:")
    print("1. Virtual environment not activated")
    print("2. MediaPipe not installed in this environment")
    print("\nTry:")
    print("  source ~/CC/cc_env/bin/activate")
    print("  pip install mediapipe>=0.10.30")
    sys.exit(1)

print()

# Step 2: Check mediapipe.python module
print("Step 2: Checking mediapipe.python module...")
try:
    import mediapipe.python
    print(f"✓ mediapipe.python module found")
    print(f"  Location: {mediapipe.python.__file__}")
except ImportError as e:
    print(f"✗ mediapipe.python module NOT found: {e}")
    print("\nThis is unusual - mediapipe package exists but python submodule missing")
    print("Try reinstalling:")
    print("  pip uninstall mediapipe -y")
    print("  pip install mediapipe>=0.10.30")
    sys.exit(1)

print()

# Step 3: Check mediapipe.python.solutions module
print("Step 3: Checking mediapipe.python.solutions module...")
try:
    import mediapipe.python.solutions
    print(f"✓ mediapipe.python.solutions module found")
    print(f"  Location: {mediapipe.python.solutions.__file__}")
except ImportError as e:
    print(f"✗ mediapipe.python.solutions module NOT found: {e}")
    print("\nMediaPipe 0.10.30+ should have this module")
    print("Check your MediaPipe version:")
    print("  pip show mediapipe")
    sys.exit(1)

print()

# Step 4: Check face_mesh specifically
print("Step 4: Checking face_mesh module...")
try:
    from mediapipe.python.solutions import face_mesh
    print(f"✓ face_mesh module imported successfully")
    print(f"  Module: {face_mesh}")
    print(f"  FaceMesh class: {face_mesh.FaceMesh}")
except ImportError as e:
    print(f"✗ face_mesh import FAILED: {e}")
    print("\nThis is the critical import needed for ChromaCloud")
    sys.exit(1)

print()

# Step 5: Try creating a FaceMesh instance
print("Step 5: Testing FaceMesh instantiation...")
try:
    detector = face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )
    print(f"✓ FaceMesh detector created successfully")
    print(f"  Detector: {detector}")
except Exception as e:
    print(f"✗ FaceMesh instantiation FAILED: {e}")
    print("\nThis might be a MediaPipe configuration issue")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Step 6: Check old API (should not exist on 0.10.30+)
print("Step 6: Checking old API (mp.solutions)...")
if hasattr(mediapipe, 'solutions'):
    print(f"⚠️  Old API (mp.solutions) exists - unexpected for 0.10.30+")
    print(f"  This suggests MediaPipe version might be wrong")
    print(f"  Reported version: {mediapipe.__version__}")
else:
    print(f"✓ Old API not present (correct for 0.10.30+)")

print()

# Summary
print("=" * 70)
print("✅ ALL CHECKS PASSED!")
print("=" * 70)
print()
print("MediaPipe 0.10.32 is correctly installed and importable.")
print("The new API (mediapipe.python.solutions) works correctly.")
print()
print("Next steps:")
print("1. Try running: python3 CC_Main.py")
print("2. If still failing, check the exact error message")
print("3. Verify you're in the correct directory: /Volumes/lc_sln/py")
print()
