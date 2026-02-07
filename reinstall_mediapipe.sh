#!/bin/bash
# MediaPipe Reinstall Script for macOS

echo "========================================================================"
echo "MediaPipe Reinstall for ChromaCloud on macOS"
echo "========================================================================"
echo ""

# Make sure we're in the virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment NOT activated!"
    echo ""
    echo "Please run:"
    echo "  source ~/CC/cc_env/bin/activate"
    echo "  bash reinstall_mediapipe.sh"
    exit 1
fi

echo "✓ Virtual environment active: $VIRTUAL_ENV"
echo ""

# Uninstall existing mediapipe
echo "Step 1: Uninstalling existing MediaPipe..."
pip uninstall mediapipe -y

# Clear pip cache to ensure fresh download
echo ""
echo "Step 2: Clearing pip cache..."
pip cache purge

# Reinstall mediapipe
echo ""
echo "Step 3: Installing MediaPipe 0.10.32..."
pip install mediapipe==0.10.32

echo ""
echo "========================================================================"
echo "Testing MediaPipe installation..."
echo "========================================================================"

# Test the installation
python3 << 'EOF'
import sys

# Test 1: Basic import
try:
    import mediapipe as mp
    print(f"✓ MediaPipe {mp.__version__} imported")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check for solutions in different locations
print("\nChecking MediaPipe API structure...")

# Try new API (0.10.15+)
try:
    from mediapipe.python.solutions import face_mesh
    print("✓ New API found: mediapipe.python.solutions")
    api_type = "new"
except ImportError:
    # Try old API (0.10.14 and earlier)
    if hasattr(mp, 'solutions'):
        from mediapipe.solutions import face_mesh
        print("✓ Old API found: mp.solutions")
        api_type = "old"
    else:
        # Try even newer API (might exist in 0.10.32)
        try:
            from mediapipe import solutions
            face_mesh = solutions.face_mesh
            print("✓ Direct solutions API found: mediapipe.solutions")
            api_type = "direct"
        except (ImportError, AttributeError):
            print("✗ No known API structure found!")
            print("\nMediaPipe version:", mp.__version__)
            print("Available attributes:", dir(mp))
            sys.exit(1)

# Test 3: Create FaceMesh instance
try:
    detector = face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )
    print(f"✓ FaceMesh instantiated successfully ({api_type} API)")
except Exception as e:
    print(f"✗ FaceMesh creation failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ MediaPipe installation successful!")
print("=" * 70)
print(f"\nAPI Type: {api_type}")
print(f"Version: {mp.__version__}")
EOF

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ SUCCESS - MediaPipe is now working!"
    echo "========================================================================"
    echo ""
    echo "Next steps:"
    echo "1. Run diagnostic again: python3 diagnose_mediapipe.py"
    echo "2. Launch ChromaCloud: python3 CC_Main.py"
else
    echo ""
    echo "========================================================================"
    echo "❌ Installation still has issues"
    echo "========================================================================"
    echo ""
    echo "Please share the output above for further troubleshooting."
fi
