"""
CUDA Configuration Test for Skin Color Matcher
Tests GPU availability and basic functionality
"""

import sys

def test_cuda_setup():
    """Test CUDA configuration"""
    print("=" * 80)
    print("CUDA配置检测")
    print("=" * 80)

    # Test PyTorch
    try:
        import torch
        print(f"✅ PyTorch版本: {torch.__version__}")

        cuda_available = torch.cuda.is_available()
        print(f"✅ CUDA可用: {cuda_available}")

        if cuda_available:
            print(f"✅ CUDA版本: {torch.version.cuda}")
            print(f"✅ GPU设备: {torch.cuda.get_device_name(0)}")
            print(f"✅ GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

            # Test tensor operation on GPU
            x = torch.randn(1000, 1000).cuda()
            y = torch.randn(1000, 1000).cuda()
            z = torch.mm(x, y)
            print(f"✅ GPU矩阵运算测试通过")

            # Clean up
            del x, y, z
            torch.cuda.empty_cache()
        else:
            print("⚠️  CUDA不可用，将使用CPU模式")
    except ImportError:
        print("❌ PyTorch未安装")
        return False

    # Test other dependencies
    try:
        import rawpy
        print(f"✅ rawpy已安装（版本: {rawpy.__version__}）")
    except ImportError:
        print("❌ rawpy未安装 - 执行: pip install rawpy")

    try:
        import cv2
        print(f"✅ OpenCV已安装（版本: {cv2.__version__}）")
    except ImportError:
        print("❌ OpenCV未安装 - 执行: pip install opencv-python")

    try:
        import matplotlib
        print(f"✅ Matplotlib已安装（版本: {matplotlib.__version__}）")
    except ImportError:
        print("❌ Matplotlib未安装 - 执行: pip install matplotlib")

    try:
        import scipy
        print(f"✅ SciPy已安装（版本: {scipy.__version__}）")
    except ImportError:
        print("❌ SciPy未安装 - 执行: pip install scipy")

    try:
        import numpy as np
        print(f"✅ NumPy已安装（版本: {np.__version__}）")
    except ImportError:
        print("❌ NumPy未安装 - 执行: pip install numpy")

    print("=" * 80)
    print("配置检测完成")
    print("=" * 80)

    return True


def test_skin_matcher_import():
    """Test skin_color_matcher import"""
    print("\n" + "=" * 80)
    print("测试SkinColorMatcher导入")
    print("=" * 80)

    try:
        from skin_color_matcher import SkinColorMatcher, ColorStats, LightroomAdjustments
        print("✅ SkinColorMatcher导入成功")

        # Test initialization
        matcher = SkinColorMatcher(use_gpu=True)
        print(f"✅ 已初始化，设备: {matcher.device}")

        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


if __name__ == "__main__":
    success = test_cuda_setup()

    if success:
        test_skin_matcher_import()

    print("\n✅ 如果所有测试通过，您可以开始使用skin_color_matcher工具了！")
    print("📝 使用示例请参考 skin_matcher_examples.py")

