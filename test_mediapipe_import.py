#!/usr/bin/env python3
"""Quick test of MediaPipe version-compatible import"""

import sys
sys.path.insert(0, '.')

try:
    from CC_SkinProcessor import (
        MEDIAPIPE_AVAILABLE,
        MEDIAPIPE_API,
        MEDIAPIPE_VERSION_INFO
    )

    print("=" * 60)
    print("MediaPipe Version-Compatible Import Test")
    print("=" * 60)
    print(f"✓ MediaPipe Available: {MEDIAPIPE_AVAILABLE}")
    print(f"✓ API Type: {MEDIAPIPE_API}")
    print(f"✓ Version Info: {MEDIAPIPE_VERSION_INFO}")
    print("=" * 60)
    print("✅ Test PASSED - Version-compatible import works!")

except Exception as e:
    print("=" * 60)
    print("❌ Test FAILED")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
