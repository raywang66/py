"""
ChromaCloud (CC) - Automated Installation Script
Author: Senior Software Architect
Date: January 2026

This script automatically detects CUDA version and installs PyTorch with
proper GPU support.
"""

import subprocess
import sys
import platform
import re
from pathlib import Path

print("=" * 70)
print("ChromaCloud - Automated Installation")
print("=" * 70)
print()

# ============================================================================
# STEP 1: Detect CUDA Version
# ============================================================================
print("STEP 1: Detecting CUDA version...")
print("-" * 70)

cuda_version = None
cuda_available = False

try:
    # Try to run nvidia-smi
    result = subprocess.run(
        ["nvidia-smi"],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.returncode == 0:
        # Parse CUDA version from output
        output = result.stdout
        match = re.search(r"CUDA Version:\s+(\d+\.\d+)", output)

        if match:
            cuda_version = match.group(1)
            cuda_available = True
            print(f"✓ CUDA detected: {cuda_version}")

            # Determine which PyTorch CUDA version to use
            cuda_major = int(cuda_version.split('.')[0])
            cuda_minor = int(cuda_version.split('.')[1])

            if cuda_major >= 12 and cuda_minor >= 1:
                pytorch_cuda = "cu121"
                print(f"✓ Will install PyTorch with CUDA 12.1 support")
            elif cuda_major >= 11 and cuda_minor >= 8:
                pytorch_cuda = "cu118"
                print(f"✓ Will install PyTorch with CUDA 11.8 support")
            else:
                pytorch_cuda = "cu118"
                print(f"⚠ CUDA {cuda_version} detected, using PyTorch CUDA 11.8")
        else:
            print("⚠ nvidia-smi found but could not parse CUDA version")
            cuda_available = False
    else:
        print("⚠ nvidia-smi not found")
        cuda_available = False

except FileNotFoundError:
    print("⚠ nvidia-smi not found - NVIDIA drivers not installed")
    cuda_available = False
except subprocess.TimeoutExpired:
    print("⚠ nvidia-smi timed out")
    cuda_available = False
except Exception as e:
    print(f"⚠ Error detecting CUDA: {e}")
    cuda_available = False

if not cuda_available:
    print()
    print("WARNING: CUDA not detected!")
    print("ChromaCloud will run in CPU mode (very slow).")
    print()
    response = input("Continue with CPU-only installation? (y/n): ").lower()

    if response != 'y':
        print("Installation cancelled.")
        sys.exit(0)

    pytorch_cuda = "cpu"
    print("✓ Will install CPU-only PyTorch")

print()

# ============================================================================
# STEP 2: Install PyTorch with CUDA Support
# ============================================================================
print("STEP 2: Installing PyTorch with GPU support...")
print("-" * 70)

if pytorch_cuda == "cpu":
    pytorch_install_cmd = [
        sys.executable, "-m", "pip", "install",
        "torch>=2.0.0",
        "torchvision>=0.15.0"
    ]
else:
    pytorch_install_cmd = [
        sys.executable, "-m", "pip", "install",
        "torch",
        "torchvision",
        "--index-url",
        f"https://download.pytorch.org/whl/{pytorch_cuda}"
    ]

print(f"Running: {' '.join(pytorch_install_cmd)}")
print()

try:
    result = subprocess.run(pytorch_install_cmd, check=True)
    print()
    print("✓ PyTorch installed successfully")
except subprocess.CalledProcessError as e:
    print(f"✗ Failed to install PyTorch: {e}")
    sys.exit(1)

print()

# ============================================================================
# STEP 3: Install Remaining Dependencies
# ============================================================================
print("STEP 3: Installing remaining dependencies...")
print("-" * 70)

requirements_file = Path(__file__).parent / "requirements_cc.txt"

if not requirements_file.exists():
    print(f"✗ requirements_cc.txt not found at {requirements_file}")
    sys.exit(1)

install_cmd = [
    sys.executable, "-m", "pip", "install",
    "-r", str(requirements_file)
]

print(f"Running: {' '.join(install_cmd)}")
print()

try:
    result = subprocess.run(install_cmd, check=True)
    print()
    print("✓ All dependencies installed successfully")
except subprocess.CalledProcessError as e:
    print(f"✗ Failed to install dependencies: {e}")
    sys.exit(1)

print()

# ============================================================================
# STEP 4: Verify Installation
# ============================================================================
print("STEP 4: Verifying installation...")
print("-" * 70)

# Test PyTorch
try:
    import torch
    print(f"✓ PyTorch {torch.__version__} installed")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"✓ CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print(f"✓ Apple Metal (MPS) available")
    else:
        print(f"⚠ No GPU acceleration available")

except ImportError as e:
    print(f"✗ PyTorch import failed: {e}")

# Test Taichi
try:
    import taichi as ti
    print(f"✓ Taichi {ti.__version__} installed")
except ImportError as e:
    print(f"✗ Taichi import failed: {e}")

# Test PySide6
try:
    from PySide6.QtCore import QT_VERSION_STR
    print(f"✓ PySide6 (Qt {QT_VERSION_STR}) installed")
except ImportError as e:
    print(f"✗ PySide6 import failed: {e}")

# Test OpenCV
try:
    import cv2
    print(f"✓ OpenCV {cv2.__version__} installed")
except ImportError as e:
    print(f"✗ OpenCV import failed: {e}")

# Test other libraries
try:
    import numpy as np
    print(f"✓ NumPy {np.__version__} installed")
except ImportError:
    pass

try:
    from PIL import Image
    print(f"✓ Pillow installed")
except ImportError:
    pass

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("INSTALLATION COMPLETE")
print("=" * 70)
print()
print("Next steps:")
print("  1. Download BiSeNet model (optional, see QUICKSTART_CC.md)")
print("  2. Run demo: python CC_demo.py")
print("  3. Launch app: python CC_MainApp.py")
print()

if pytorch_cuda == "cpu":
    print("⚠ WARNING: Running in CPU mode - performance will be very slow!")
    print("  Install NVIDIA drivers and CUDA Toolkit for GPU acceleration")
    print()

print("=" * 70)

