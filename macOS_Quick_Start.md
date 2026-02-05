# Quick Start on Your macOS

## When You Pull ChromaCloud from GitHub

```bash
# 1. Pull the latest code
cd ~/path/to/ChromaCloud  # wherever you clone it
git pull origin main

# 2. Navigate to Python directory
cd py

# 3. Create isolated virtual environment (RECOMMENDED)
python3 install_cc.py --venv

# This creates venv_chromacloud/ and exits
# You'll see instructions to activate

# 4. Activate the virtual environment
source venv_chromacloud/bin/activate

# Your prompt should now show: (venv_chromacloud)

# 5. Install ChromaCloud
python3 install_cc.py

# This will:
# - Detect Apple Silicon and enable MPS
# - Install PyTorch with Metal support
# - Install all dependencies from requirements_cc_macos.txt
# - Verify GPU acceleration is working

# 6. Run ChromaCloud
python3 CC_Main.py
```

## One-Liner (Copy-Paste)

```bash
cd ~/path/to/ChromaCloud/py && \
python3 install_cc.py --venv && \
source venv_chromacloud/bin/activate && \
python3 install_cc.py
```

## Expected Output on Apple Silicon

```
======================================================================
ChromaCloud - Automated Installation
======================================================================

Operating System: Darwin
Platform: macOS-14.0-arm64-arm-64bit
Python: 3.11.x

✓ Running in virtual environment
  Location: /Users/yourname/ChromaCloud/py/venv_chromacloud

STEP 1: Detecting GPU support...
----------------------------------------------------------------------
Checking for Apple Silicon (MPS support)...
CPU: Apple M1/M2/M3/M4
✓ Apple Silicon detected - MPS acceleration available

STEP 2: Installing PyTorch with GPU support...
----------------------------------------------------------------------
Installing PyTorch with MPS support for Apple Silicon...
✓ PyTorch installed successfully

STEP 3: Installing remaining dependencies...
----------------------------------------------------------------------
Using: requirements_cc_macos.txt
✓ All dependencies installed successfully

STEP 4: Verifying installation...
----------------------------------------------------------------------
✓ PyTorch 2.x.x installed
✓ Apple Metal (MPS) available: True
✓ GPU acceleration: Enabled (Apple Silicon)
✓ Taichi x.x.x installed
✓ PySide6 (Qt x.x.x) installed
✓ OpenCV x.x.x installed
✓ NumPy x.x.x installed
✓ Pillow installed

======================================================================
INSTALLATION COMPLETE
======================================================================

Next steps:
  1. Run ChromaCloud: python3 CC_Main.py
  2. Check GPU status in app logs (should show MPS if Apple Silicon)
  3. See INSTALL_MACOS.md for macOS-specific tips

✓ Apple Silicon GPU acceleration enabled!
  ChromaCloud will use Metal Performance Shaders (MPS)

======================================================================
```

## Create a Shell Alias (Optional but Convenient)

```bash
# Add to ~/.zshrc (macOS default shell)
echo "alias chromacloud='cd ~/path/to/ChromaCloud/py && source venv_chromacloud/bin/activate && python3 CC_Main.py'" >> ~/.zshrc

# Reload shell config
source ~/.zshrc

# Now you can just run:
chromacloud
```

## Files You'll See

```
ChromaCloud/py/
├── venv_chromacloud/          ← NEW! Your isolated environment
│   ├── bin/activate           ← Activation script
│   └── lib/python3.11/site-packages/  ← All packages isolated here
├── requirements_cc_macos.txt  ← NEW! macOS-specific requirements
├── INSTALL_MACOS.md           ← NEW! Full installation guide
├── README_MACOS.md            ← NEW! Quick start guide
├── install_cc.py              ← UPDATED! Now supports --venv
├── CC_Main.py
└── ... (other ChromaCloud files)
```

## Verifying Isolation

```bash
# Check you're using virtual environment Python
which python
# Should show: /path/to/ChromaCloud/py/venv_chromacloud/bin/python

# Check PyTorch is in the venv
python -c "import torch; print(torch.__file__)"
# Should show: /path/to/ChromaCloud/py/venv_chromacloud/lib/...

# Check MPS is available
python -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"
# Should show: MPS: True
```

## Deactivating Virtual Environment

```bash
# When you're done with ChromaCloud
deactivate

# Your prompt returns to normal (no venv prefix)
# System Python is unaffected!
```

---

**Your ChromaCloud is now fully isolated on macOS!** ✅

All packages (PyTorch, PySide6, etc.) are in `venv_chromacloud/` and won't interfere with your system Python or other projects.
