"""
ChromaCloud (CC) - Automated Installation Script
Author: Senior Software Architect
Date: January 2026

This script automatically detects system configuration and installs PyTorch with
proper GPU support:
- Windows/Linux: CUDA support (NVIDIA GPU)
- macOS: MPS support (Apple Silicon M1/M2/M3/M4)

Usage:
    python install_cc.py              # Install to current Python environment
    python install_cc.py --venv       # Create and use virtual environment (recommended)
"""

import subprocess
import sys
import platform
import re
import venv
from pathlib import Path

print("=" * 70)
print("ChromaCloud - Automated Installation")
print("=" * 70)
print()

# Detect operating system
os_type = platform.system()
print(f"Operating System: {os_type}")
print(f"Platform: {platform.platform()}")
print(f"Python: {sys.version}")
print()

# ============================================================================
# STEP 0: Virtual Environment Setup (Optional but Recommended)
# ============================================================================
use_venv = "--venv" in sys.argv or "-v" in sys.argv

# Check if already in a virtual environment
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

if use_venv and not in_venv:
    print("STEP 0: Setting up virtual environment...")
    print("-" * 70)

    venv_name = "cc_env"
    venv_path = Path(__file__).parent / venv_name

    if venv_path.exists():
        print(f"✓ Virtual environment already exists: {venv_path}")
    else:
        print(f"Creating virtual environment: {venv_path}")
        try:
            venv.create(venv_path, with_pip=True)
            print(f"✓ Virtual environment created successfully")
        except Exception as e:
            print(f"✗ Failed to create virtual environment: {e}")
            print("  Continuing with system Python...")
            use_venv = False

    if use_venv:
        # Determine activation command based on OS
        if os_type == "Windows":
            activate_script = venv_path / "Scripts" / "activate.bat"
            activate_cmd = str(activate_script)
        else:  # macOS/Linux
            activate_script = venv_path / "bin" / "activate"
            activate_cmd = f"source {activate_script}"

        print()
        print("=" * 70)
        print("VIRTUAL ENVIRONMENT CREATED")
        print("=" * 70)
        print()
        print(f"To activate the virtual environment, run:")
        if os_type == "Windows":
            print(f"  {venv_path}\\Scripts\\activate")
        else:
            print(f"  source {venv_path}/bin/activate")
        print()
        print("Then re-run this script:")
        print(f"  python install_cc.py")
        print()
        print("Or activate and continue in one command:")
        if os_type == "Windows":
            print(f"  {venv_path}\\Scripts\\activate && python install_cc.py")
        else:
            print(f"  source {venv_path}/bin/activate && python install_cc.py")
        print()
        print("=" * 70)
        sys.exit(0)

elif in_venv:
    print("✓ Running in virtual environment")
    print(f"  Location: {sys.prefix}")
    print()
elif not use_venv:
    print("⚠ Installing to system Python (not isolated)")
    print("  Tip: Use 'python install_cc.py --venv' for isolated installation")
    print()
    response = input("Continue with system Python? (y/n): ").lower()
    if response != 'y':
        print()
        print("Installation cancelled. Run with --venv flag:")
        print(f"  python install_cc.py --venv")
        sys.exit(0)
    print()

# ============================================================================
# STEP 1: Detect GPU Support
# ============================================================================
print("STEP 1: Detecting GPU support...")
print("-" * 70)

cuda_version = None
cuda_available = False
mps_available = False
gpu_type = "none"
pytorch_cuda = None  # Will be set for CUDA installations

# Check for macOS with Apple Silicon (MPS support)
if os_type == "Darwin":  # macOS
    print("Checking for Apple Silicon (MPS support)...")

    try:
        # Check if running on Apple Silicon
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            timeout=5
        )

        cpu_brand = result.stdout.strip()
        print(f"CPU: {cpu_brand}")

        if "Apple" in cpu_brand:
            mps_available = True
            gpu_type = "mps"
            print(f"✓ Apple Silicon detected - MPS acceleration available")
        else:
            print(f"⚠ Intel Mac detected - CPU mode only")
            gpu_type = "cpu"

    except Exception as e:
        print(f"⚠ Could not detect CPU type: {e}")
        print(f"  Assuming Apple Silicon and will install with MPS support")
        mps_available = True
        gpu_type = "mps"

# Check for CUDA on Windows/Linux
elif os_type in ["Windows", "Linux"]:
    print("Checking for CUDA (NVIDIA GPU)...")

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
                gpu_type = "cuda"
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
                gpu_type = "cpu"
        else:
            print("⚠ nvidia-smi not found")
            cuda_available = False
            gpu_type = "cpu"

    except FileNotFoundError:
        print("⚠ nvidia-smi not found - NVIDIA drivers not installed")
        cuda_available = False
        gpu_type = "cpu"
    except subprocess.TimeoutExpired:
        print("⚠ nvidia-smi timed out")
        cuda_available = False
        gpu_type = "cpu"
    except Exception as e:
        print(f"⚠ Error detecting CUDA: {e}")
        cuda_available = False
        gpu_type = "cpu"

else:
    print(f"⚠ Unknown operating system: {os_type}")
    gpu_type = "cpu"


# Handle CPU-only installation warnings
if gpu_type == "cpu":
    print()
    print("WARNING: No GPU acceleration detected!")
    print("ChromaCloud will run in CPU mode (slower performance).")
    print()

    if os_type == "Darwin":
        print("Note: If you have an Apple Silicon Mac, PyTorch should")
        print("automatically detect MPS support after installation.")
        print()

    response = input("Continue with CPU installation? (y/n): ").lower()

    if response != 'y':
        print("Installation cancelled.")
        sys.exit(0)

    print("✓ Will install CPU PyTorch (with auto-detection for MPS)")

print()

# ============================================================================
# STEP 2: Install PyTorch with GPU Support
# ============================================================================
print("STEP 2: Installing PyTorch with GPU support...")
print("-" * 70)

# Determine PyTorch installation command based on GPU type
if gpu_type == "mps" or (gpu_type == "cpu" and os_type == "Darwin"):
    # macOS: Install standard PyTorch (includes MPS support)
    pytorch_install_cmd = [
        sys.executable, "-m", "pip", "install",
        "torch>=2.0.0",
        "torchvision>=0.15.0"
    ]
    print("Installing PyTorch with MPS support for Apple Silicon...")

elif gpu_type == "cuda" and cuda_available:
    # Windows/Linux with CUDA
    pytorch_install_cmd = [
        sys.executable, "-m", "pip", "install",
        "torch",
        "torchvision",
        "--index-url",
        f"https://download.pytorch.org/whl/{pytorch_cuda}"
    ]
    print(f"Installing PyTorch with CUDA {pytorch_cuda} support...")

else:
    # CPU-only installation
    pytorch_install_cmd = [
        sys.executable, "-m", "pip", "install",
        "torch>=2.0.0",
        "torchvision>=0.15.0"
    ]
    print("Installing CPU-only PyTorch...")

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

# Select appropriate requirements file
if os_type == "Darwin":
    requirements_file = Path(__file__).parent / "requirements_cc_macos.txt"
    if not requirements_file.exists():
        print("⚠ requirements_cc_macos.txt not found, using requirements_cc.txt")
        requirements_file = Path(__file__).parent / "requirements_cc.txt"
else:
    requirements_file = Path(__file__).parent / "requirements_cc.txt"

if not requirements_file.exists():
    print(f"✗ {requirements_file.name} not found at {requirements_file}")
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

    # Check GPU acceleration
    if torch.cuda.is_available():
        print(f"✓ CUDA available: True")
        print(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"✓ CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print(f"✓ Apple Metal (MPS) available: True")
        print(f"✓ GPU acceleration: Enabled (Apple Silicon)")
    else:
        print(f"⚠ GPU acceleration: Not available (CPU mode)")
        if os_type == "Darwin":
            print(f"  Note: MPS requires macOS 12.3+ and Apple Silicon")

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
if os_type == "Darwin":
    print("  1. Run ChromaCloud: python3 CC_Main.py")
    print("  2. Check GPU status in app logs (should show MPS if Apple Silicon)")
    print("  3. See INSTALL_MACOS.md for macOS-specific tips")
else:
    print("  1. Download BiSeNet model (optional, see QUICKSTART_CC.md)")
    print("  2. Run demo: python CC_demo.py")
    print("  3. Launch app: python CC_Main.py")
print()

# System-specific warnings
if gpu_type == "cpu":
    if os_type == "Darwin":
        print("⚠ WARNING: Running in CPU mode on macOS")
        print("  For best performance, use Apple Silicon Mac (M1/M2/M3/M4)")
        print()
    else:
        print("⚠ WARNING: Running in CPU mode - performance will be slower!")
        print("  Install NVIDIA drivers and CUDA Toolkit for GPU acceleration")
        print()
elif gpu_type == "mps":
    print("✓ Apple Silicon GPU acceleration enabled!")
    print("  ChromaCloud will use Metal Performance Shaders (MPS)")
    print()
elif gpu_type == "cuda":
    print("✓ NVIDIA GPU acceleration enabled!")
    print("  ChromaCloud will use CUDA for AI processing")
    print()

print("=" * 70)

