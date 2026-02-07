#!/bin/bash
# Downgrade MediaPipe to compatible version

echo "========================================================================"
echo "MediaPipe Downgrade to Compatible Version"
echo "========================================================================"
echo ""

# Check if in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment NOT activated!"
    echo ""
    echo "Please run:"
    echo "  source ~/CC/cc_env/bin/activate"
    echo "  bash downgrade_mediapipe.sh"
    exit 1
fi

echo "✓ Virtual environment active: $VIRTUAL_ENV"
echo ""

echo "Current MediaPipe version:"
pip show mediapipe | grep Version

echo ""
echo "Reason for downgrade:"
echo "MediaPipe 0.10.30+ removed the legacy API that ChromaCloud uses."
echo "We need to install a version with the legacy face_mesh API."
echo ""

# Uninstall current version
echo "Step 1: Uninstalling MediaPipe 0.10.32..."
pip uninstall mediapipe -y

# Clear cache
echo ""
echo "Step 2: Clearing pip cache..."
pip cache purge

# Try to find a compatible version
echo ""
echo "Step 3: Finding compatible MediaPipe version..."
echo ""

# Try versions in order of preference
VERSIONS=("0.10.9" "0.10.7" "0.10.5" "0.10.3" "0.10.1" "0.10.0")

for VERSION in "${VERSIONS[@]}"; do
    echo "Trying MediaPipe $VERSION..."

    # Try to install
    if pip install mediapipe==$VERSION 2>&1 | grep -q "Successfully installed"; then
        echo "✓ MediaPipe $VERSION installed"

        # Test if it has the legacy API
        echo "Testing legacy API..."
        TEST_RESULT=$(python3 << 'EOF'
import sys
try:
    import mediapipe as mp

    # Try mp.solutions (0.10.14 and earlier)
    if hasattr(mp, 'solutions'):
        from mediapipe.solutions import face_mesh
        print("mp.solutions")
        sys.exit(0)

    # Try mediapipe.python.solutions (0.10.15+)
    try:
        from mediapipe.python.solutions import face_mesh
        print("python.solutions")
        sys.exit(0)
    except ImportError:
        pass

    # No legacy API found
    print("none")
    sys.exit(1)
except Exception as e:
    print(f"error: {e}")
    sys.exit(1)
EOF
)

        if [ $? -eq 0 ]; then
            echo "✓ Legacy API found: $TEST_RESULT"
            echo ""
            echo "========================================================================"
            echo "✅ SUCCESS!"
            echo "========================================================================"
            echo ""
            echo "MediaPipe $VERSION is compatible with ChromaCloud"
            echo "API type: $TEST_RESULT"
            echo ""
            echo "Next steps:"
            echo "1. Run diagnostic: python3 diagnose_mediapipe.py"
            echo "2. Launch ChromaCloud: python3 CC_Main.py"
            exit 0
        else
            echo "✗ Legacy API not found in $VERSION"
            pip uninstall mediapipe -y
        fi
    else
        echo "✗ MediaPipe $VERSION not available on this platform"
    fi

    echo ""
done

# If we get here, no compatible version was found
echo "========================================================================"
echo "❌ No compatible MediaPipe version found"
echo "========================================================================"
echo ""
echo "None of the tested versions (${VERSIONS[@]}) are available on macOS"
echo "or have the legacy API."
echo ""
echo "Available versions on macOS (from your previous check):"
echo "  0.10.30, 0.10.31, 0.10.32"
echo ""
echo "All of these use the new tasks API which ChromaCloud doesn't support yet."
echo ""
echo "OPTIONS:"
echo "1. Wait for ChromaCloud to add tasks API support (requires code refactoring)"
echo "2. Check if any older versions become available"
echo "3. Use ChromaCloud on Windows (which has MediaPipe 0.10.14 available)"
echo ""
exit 1
