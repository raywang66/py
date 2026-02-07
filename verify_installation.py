#!/usr/bin/env python3
"""
ChromaCloud Installation Verification Script
Tests all critical components after installation
"""

import sys

def test_component(name, test_func):
    """Test a component and print result"""
    try:
        result = test_func()
        print(f"✓ {name}: {result}")
        return True
    except Exception as e:
        print(f"✗ {name}: FAILED - {e}")
        return False

def main():
    print("=" * 70)
    print("ChromaCloud Installation Verification")
    print("=" * 70)
    print()

    results = {}

    # Test Python version
    results['python'] = test_component(
        "Python Version",
        lambda: f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # Test PyTorch
    results['pytorch'] = test_component(
        "PyTorch",
        lambda: __import__('torch').__version__
    )

    # Test PyTorch MPS (macOS GPU)
    def test_mps():
        import torch
        if torch.backends.mps.is_available():
            return "Available (Apple Silicon GPU)"
        else:
            return "Not available (CPU only)"

    results['mps'] = test_component("Apple Metal (MPS)", test_mps)

    # Test Taichi
    results['taichi'] = test_component(
        "Taichi",
        lambda: __import__('taichi').__version__
    )

    # Test PySide6
    def test_pyside6():
        import PySide6
        from PySide6 import QtCore
        try:
            version = QtCore.QT_VERSION_STR
        except AttributeError:
            try:
                version = QtCore.qVersion()
            except:
                version = PySide6.__version__
        return version

    results['pyside6'] = test_component("PySide6 (Qt)", test_pyside6)

    # Test OpenCV
    results['opencv'] = test_component(
        "OpenCV",
        lambda: __import__('cv2').__version__
    )

    # Test NumPy
    results['numpy'] = test_component(
        "NumPy",
        lambda: __import__('numpy').__version__
    )

    # Test Pillow
    def test_pillow():
        from PIL import Image
        return Image.__version__ if hasattr(Image, '__version__') else "OK"

    results['pillow'] = test_component("Pillow", test_pillow)

    # Test MediaPipe (CRITICAL for ChromaCloud)
    def test_mediapipe():
        import mediapipe as mp

        # Test version-compatible import
        try:
            from mediapipe.python.solutions import face_mesh
            api = "new (mediapipe.python.solutions)"
        except ImportError:
            if hasattr(mp, 'solutions'):
                api = "old (mp.solutions)"
            else:
                raise ImportError("No supported API found")

        return f"{mp.__version__} - API: {api}"

    results['mediapipe'] = test_component("MediaPipe", test_mediapipe)

    # Test CC_SkinProcessor import
    def test_cc_skinprocessor():
        sys.path.insert(0, '.')
        from CC_SkinProcessor import (
            MEDIAPIPE_AVAILABLE,
            MEDIAPIPE_API,
            MEDIAPIPE_VERSION_INFO
        )

        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe not available in CC_SkinProcessor")

        return f"{MEDIAPIPE_API} API - {MEDIAPIPE_VERSION_INFO}"

    results['cc_skinprocessor'] = test_component(
        "CC_SkinProcessor",
        test_cc_skinprocessor
    )

    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED - ChromaCloud is ready to use!")
        return 0
    else:
        print("⚠️  Some tests failed - check errors above")
        failed = [name for name, result in results.items() if not result]
        print(f"Failed components: {', '.join(failed)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
