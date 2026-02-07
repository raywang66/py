#!/bin/bash
# Quick MediaPipe Diagnostic - Run this on macOS

echo "========================================================================"
echo "ChromaCloud MediaPipe Quick Diagnostic"
echo "========================================================================"
echo ""

# Check if in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment NOT activated!"
    echo ""
    echo "Fix:"
    echo "  source ~/CC/cc_env/bin/activate"
    echo ""
    exit 1
else
    echo "✓ Virtual environment active: $VIRTUAL_ENV"
fi

# Check Python location
PYTHON_PATH=$(which python3)
echo "✓ Python: $PYTHON_PATH"

# Check current directory
CURRENT_DIR=$(pwd)
echo "✓ Current directory: $CURRENT_DIR"

# Check if CC_SkinProcessor.py exists
if [ -f "CC_SkinProcessor.py" ]; then
    echo "✓ CC_SkinProcessor.py found"
else
    echo "❌ CC_SkinProcessor.py NOT found in current directory"
    echo ""
    echo "Fix:"
    echo "  cd /Volumes/lc_sln/py"
    echo ""
    exit 1
fi

echo ""
echo "Testing MediaPipe imports..."
echo "------------------------------------------------------------------------"

# Test MediaPipe import
python3 << 'EOF'
import sys

try:
    import mediapipe as mp
    print(f"✓ mediapipe {mp.__version__} imported")
except ImportError as e:
    print(f"❌ mediapipe import FAILED: {e}")
    sys.exit(1)

try:
    from mediapipe.python.solutions import face_mesh
    print(f"✓ face_mesh imported (new API)")
except ImportError as e:
    print(f"❌ face_mesh import FAILED: {e}")
    print("")
    print("This means MediaPipe 0.10.30+ API is not available")
    print("Try reinstalling:")
    print("  pip uninstall mediapipe -y")
    print("  pip install mediapipe>=0.10.30")
    sys.exit(1)

try:
    fm = face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)
    print(f"✓ FaceMesh instantiated")
except Exception as e:
    print(f"❌ FaceMesh instantiation FAILED: {e}")
    sys.exit(1)

try:
    from CC_SkinProcessor import MEDIAPIPE_AVAILABLE, MEDIAPIPE_API
    print(f"✓ CC_SkinProcessor imported")
    print(f"  MEDIAPIPE_AVAILABLE: {MEDIAPIPE_AVAILABLE}")
    print(f"  MEDIAPIPE_API: {MEDIAPIPE_API}")
except ImportError as e:
    print(f"❌ CC_SkinProcessor import FAILED: {e}")
    sys.exit(1)

print("")
print("========================================================================")
print("✅ ALL CHECKS PASSED - MediaPipe is working correctly!")
print("========================================================================")
print("")
print("You can now run ChromaCloud:")
print("  python3 CC_Main.py")
EOF

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo ""
    echo "========================================================================"
    echo "❌ Diagnostic FAILED"
    echo "========================================================================"
    echo ""
    echo "For detailed diagnostics, run:"
    echo "  python3 diagnose_mediapipe.py"
    echo ""
    echo "For troubleshooting guide, see:"
    echo "  MEDIAPIPE_IMPORT_TROUBLESHOOTING.md"
    echo ""
    exit 1
fi
