# ChromaCloud Installation Guide for macOS

## Prerequisites

### 1. System Requirements
- **macOS 12.0 (Monterey)** or later
- **Apple Silicon (M1/M2/M3/M4)** recommended for GPU acceleration
- **8GB RAM** minimum (16GB+ recommended for large RAW files)
- **Python 3.10 or 3.11** (best compatibility with PyTorch MPS)

### 2. Check Your System
```bash
# Check macOS version and chip type
system_profiler SPSoftwareDataType SPHardwareDataType | grep -E "System Version|Chip"

# Check Python version
python3 --version
```

### 3. Install Xcode Command Line Tools
```bash
xcode-select --install
```

### 4. Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Installation Steps

### Method 1: Automated Installation with Virtual Environment (Recommended)

```bash
# Clone the repository
cd ~/Projects  # or your preferred directory
git clone https://github.com/YOUR_USERNAME/ChromaCloud.git
cd ChromaCloud/py

# Create and activate virtual environment (recommended for isolation)
python3 install_cc.py --venv

# This will create venv_chromacloud/ and show activation command
# Activate it:
source venv_chromacloud/bin/activate

# Then install ChromaCloud
python3 install_cc.py
```

**Why use virtual environment?**
- ✓ Isolated from system Python packages
- ✓ Won't conflict with other Python projects
- ✓ Easy to remove (just delete venv_chromacloud/)
- ✓ Recommended best practice for Python projects

### Method 2: Manual Installation

#### Step 1: Install System Dependencies
```bash
# Install RAW file support libraries
brew install libraw libjpeg libtiff
```

#### Step 2: Create Virtual Environment (Recommended)
```bash
# Navigate to ChromaCloud directory
cd ~/Projects/ChromaCloud/py

# Create virtual environment
python3 -m venv venv_chromacloud

# Activate virtual environment
source venv_chromacloud/bin/activate

# Verify you're in the virtual environment (should see (venv_chromacloud) in prompt)
which python
```

#### Step 3: Install PyTorch with MPS Support
```bash
# For Apple Silicon (M1/M2/M3/M4) - includes GPU acceleration via Metal
pip install torch torchvision

# Verify MPS (Metal Performance Shaders) is available
python3 -c "import torch; print(f'MPS Available: {torch.backends.mps.is_available()}')"
```

**Expected Output:**
```
MPS Available: True
```

#### Step 4: Install ChromaCloud Dependencies
```bash
pip install -r requirements_cc_macos.txt
```

#### Step 5: Verify Installation
```bash
python3 -c "
import torch
import mediapipe
import taichi as ti
import PySide6
print('✓ PyTorch:', torch.__version__)
print('✓ MPS Available:', torch.backends.mps.is_available())
print('✓ MediaPipe:', mediapipe.__version__)
print('✓ Taichi:', ti.__version__)
print('✓ PySide6:', PySide6.__version__)
"
```

## GPU Acceleration on macOS

### Apple Silicon (M1/M2/M3/M4)
ChromaCloud leverages multiple GPU acceleration technologies on Apple Silicon:

1. **PyTorch MPS (Metal Performance Shaders)**
   - Used for face detection and skin analysis
   - Automatically enabled on Apple Silicon
   - 2-5x faster than CPU

2. **Taichi Metal Backend**
   - Used for 3D HSL visualization rendering
   - Renders 50,000+ points in real-time
   - Automatically uses Metal on macOS

3. **Apple Neural Engine**
   - MediaPipe face detection utilizes ANE when available
   - Extremely efficient for face mesh analysis

### Intel Mac
- **CPU-only mode** (no CUDA support on macOS)
- Still functional but slower for large images
- Consider upgrading to Apple Silicon for best performance

## Running ChromaCloud

```bash
# Activate virtual environment (if using)
source venv_chromacloud/bin/activate

# Run ChromaCloud
python3 CC_Main.py
```

## Troubleshooting

### Issue: "MPS Available: False" on Apple Silicon
```bash
# Check macOS version (MPS requires macOS 12.3+)
sw_vers

# Update PyTorch to latest version
pip install --upgrade torch torchvision
```

### Issue: rawpy installation fails
```bash
# Install libraw via Homebrew
brew install libraw

# Reinstall rawpy
pip uninstall rawpy
pip install rawpy --no-cache-dir
```

### Issue: PySide6 GUI doesn't appear
```bash
# Check if running via SSH (GUI won't work)
echo $SSH_CONNECTION

# If local, reinstall PySide6
pip uninstall PySide6 PySide6-Addons
pip install PySide6 PySide6-Addons --no-cache-dir
```

### Issue: Permission denied for folder watching
```bash
# Grant Python full disk access in System Preferences
# System Preferences > Security & Privacy > Privacy > Full Disk Access
# Add your Terminal app or Python executable
```

## Performance Optimization Tips

1. **Use SSD for Database**
   - Place `chromacloud.db` on fast SSD
   - Significantly improves thumbnail loading

2. **Allocate More Memory**
   - Close other apps when processing large RAW files
   - ChromaCloud benefits from unified memory on Apple Silicon

3. **Enable Metal GPU Acceleration**
   - Verify MPS is enabled for PyTorch
   - Verify Taichi is using Metal backend:
     ```python
     import taichi as ti
     ti.init(arch=ti.metal)
     print(ti.cfg.arch)  # Should show: metal
     ```

4. **Optimize for Large Libraries**
   - Enable lazy loading (default in v1.2+)
   - Use batch analysis for folders with 100+ images

## macOS-Specific Features

- **Native FSEvents**: Faster folder monitoring than generic watchdog
- **Spotlight Integration**: ChromaCloud respects .nosync folders
- **Retina Display Support**: High-DPI UI rendering
- **Touch Bar Support**: Quick access to common functions (if available)
- **Dark Mode**: Automatically follows system appearance

## Updating ChromaCloud

```bash
# Navigate to ChromaCloud directory
cd ~/Projects/ChromaCloud/py

# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements_cc_macos.txt

# Restart ChromaCloud
python3 CC_Main.py
```

## Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove ChromaCloud directory
rm -rf ~/Projects/ChromaCloud

# Remove virtual environment
rm -rf venv_chromacloud

# (Optional) Remove Homebrew dependencies
brew uninstall libraw libjpeg libtiff
```

## Support

For issues specific to macOS installation, please check:
- [GitHub Issues](https://github.com/YOUR_USERNAME/ChromaCloud/issues)
- [Documentation](https://github.com/YOUR_USERNAME/ChromaCloud/wiki)

---

**Note**: ChromaCloud is optimized for Apple Silicon Macs. Intel Macs will work but with reduced performance for AI and 3D rendering tasks.
