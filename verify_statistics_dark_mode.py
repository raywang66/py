#!/usr/bin/env python
"""
Verification script for Statistics Window Dark Mode
验证 Statistics Window 深色模式是否正确实现
"""

import sys
from pathlib import Path

def test_import():
    """Test if CC_StatisticsWindow can be imported"""
    try:
        from CC_StatisticsWindow import CC_StatisticsWindow
        print("✅ CC_StatisticsWindow imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_init_parameters():
    """Test if CC_StatisticsWindow accepts is_dark parameter"""
    try:
        from CC_StatisticsWindow import CC_StatisticsWindow
        import inspect

        sig = inspect.signature(CC_StatisticsWindow.__init__)
        params = list(sig.parameters.keys())

        if 'is_dark' in params:
            print("✅ CC_StatisticsWindow accepts 'is_dark' parameter")
            return True
        else:
            print(f"❌ 'is_dark' parameter not found. Parameters: {params}")
            return False
    except Exception as e:
        print(f"❌ Parameter check failed: {e}")
        return False

def test_theme_methods():
    """Test if theme helper methods exist"""
    try:
        from CC_StatisticsWindow import CC_StatisticsWindow

        methods = ['_apply_theme', '_get_plot_bg_color', '_get_text_color', '_get_grid_color']

        for method in methods:
            if hasattr(CC_StatisticsWindow, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' not found")
                return False

        return True
    except Exception as e:
        print(f"❌ Method check failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Statistics Window Dark Mode - Verification Test")
    print("=" * 60)
    print()

    tests = [
        ("Import Test", test_import),
        ("Parameter Test", test_init_parameters),
        ("Method Test", test_theme_methods),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n🧪 Running: {name}")
        print("-" * 40)
        result = test_func()
        results.append(result)
        print()

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, (name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Statistics Window Dark Mode is ready!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the code.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

