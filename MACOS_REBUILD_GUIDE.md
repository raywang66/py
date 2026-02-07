# ChromaCloud macOS Environment Rebuild Guide

**Date:** February 6, 2026  
**Issue:** MediaPipe 0.10.32 incompatibility on macOS  
**Solution:** Rebuild with MediaPipe 0.10.14 (pinned version)

---

## What Changed

Both `requirements_cc.txt` and `requirements_cc_macos.txt` have been updated to pin MediaPipe to version **0.10.14**:

```txt
# OLD (flexible, caused version mismatch):
mediapipe>=0.10.0

# NEW (pinned for compatibility):
mediapipe==0.10.14
```

### Why 0.10.14?

- ✅ **API Compatible** - Has `mp.solutions` namespace that ChromaCloud uses
- ✅ **Lighter Dependencies** - No jax/jaxlib (saves 500MB+)
- ✅ **Better Compatibility** - Works with PyTorch and Taichi without conflicts
- ✅ **Cross-Platform** - Same version on Windows and macOS = consistent behavior
- ✅ **Proven Stable** - Tested and working on Windows

---

## macOS Rebuild Steps

### Step 1: Remove Old Virtual Environment

```bash
# Navigate to ChromaCloud directory
cd ~/Projects/ChromaCloud/py  # or wherever your project is

# Deactivate virtual environment if active
deactivate

# Remove old virtual environment
rm -rf cc_env
```

### Step 2: Clean pip Cache (Optional but Recommended)

```bash
# Clear pip cache to ensure fresh downloads
pip cache purge
```

### Step 3: Rebuild Virtual Environment

```bash
# Run the automated installer with venv option
python3 install_cc.py --venv

# This will:
# 1. Create new cc_env/ directory
# 2. Install PyTorch with MPS support
# 3. Install MediaPipe 0.10.14 (pinned)
# 4. Install all other dependencies
```

### Step 4: Activate and Verify

```bash
# Activate the virtual environment
source cc_env/bin/activate

# Verify MediaPipe version
python3 -c "import mediapipe as mp; print(f'MediaPipe: {mp.__version__}'); print(f'Has solutions: {hasattr(mp, \"solutions\")}')"

# Expected output:
# MediaPipe: 0.10.14
# Has solutions: True
```

### Step 5: Test ChromaCloud

```bash
# Run the demo to verify everything works
python3 CC_demo.py

# Launch the full application
python3 CC_Main.py
```

---

## Verification Checklist

After rebuild, verify:

- [ ] Virtual environment created: `cc_env/` directory exists
- [ ] MediaPipe version is **0.10.14**
- [ ] `mp.solutions` attribute exists (returns True)
- [ ] PyTorch installed with MPS support
- [ ] Taichi installed for 3D rendering
- [ ] PySide6 (Qt6) installed for UI
- [ ] CC_demo.py runs without errors
- [ ] CC_Main.py launches successfully

---

## Quick Rebuild Command (One-Liner)

If you're confident and want to rebuild quickly:

```bash
cd ~/Projects/ChromaCloud/py && \
rm -rf cc_env && \
python3 install_cc.py --venv && \
source cc_env/bin/activate && \
python3 -c "import mediapipe as mp; print(f'✓ MediaPipe {mp.__version__} - Has solutions: {hasattr(mp, \"solutions\")}')"
```

---

## Troubleshooting

### Issue: Still Getting 0.10.32

**Solution:** Clear pip cache and try again:
```bash
pip cache purge
rm -rf cc_env
python3 install_cc.py --venv
```

### Issue: Dependency Conflicts

**Solution:** The pinned version should avoid conflicts, but if issues persist:
```bash
# Check for conflicting packages
pip list | grep -E "(protobuf|numpy|jax)"

# If jax/jaxlib are installed, remove them (not needed with 0.10.14)
pip uninstall jax jaxlib -y
pip install mediapipe==0.10.14
```

### Issue: Import Error

If you see `AttributeError: module 'mediapipe' has no attribute 'solutions'`:

```bash
# Check actual installed version
pip show mediapipe | grep Version

# If not 0.10.14, force reinstall
pip uninstall mediapipe -y
pip install mediapipe==0.10.14
```

---

## What This Fixes

### Before (Broken on macOS):
```python
import mediapipe as mp
mp_face_mesh = mp.solutions.face_mesh  # ❌ AttributeError with 0.10.32
```

### After (Works on macOS):
```python
import mediapipe as mp
mp_face_mesh = mp.solutions.face_mesh  # ✅ Works with 0.10.14
```

---

## Expected Installation Output

When running `install_cc.py --venv`, you should see:

```
======================================================================
ChromaCloud - Automated Installation
======================================================================

Operating System: Darwin
Platform: macOS-14.x-arm64-arm-64bit
Python: 3.11.x

STEP 0: Setting up virtual environment...
----------------------------------------------------------------------
Creating virtual environment: /Users/yourname/Projects/ChromaCloud/py/cc_env
✓ Virtual environment created successfully

======================================================================
VIRTUAL ENVIRONMENT CREATED
======================================================================

To activate the virtual environment, run:
  source /Users/yourname/Projects/ChromaCloud/py/cc_env/bin/activate

Then re-run this script:
  python install_cc.py
```

After reactivating and running again:

```
STEP 1: Detecting GPU acceleration support...
----------------------------------------------------------------------
CPU: Apple M1/M2/M3 (or similar)
✓ Apple Silicon detected - MPS acceleration available

STEP 2: Installing PyTorch with GPU support...
----------------------------------------------------------------------
Installing PyTorch with MPS support for Apple Silicon...
✓ PyTorch installed successfully

STEP 3: Installing remaining dependencies...
----------------------------------------------------------------------
Running: python -m pip install -r requirements_cc_macos.txt
✓ All dependencies installed successfully

STEP 4: Verifying installation...
----------------------------------------------------------------------
✓ PyTorch 2.x.x installed
✓ Apple Metal (MPS) available: True
✓ GPU acceleration: Enabled (Apple Silicon)
✓ Taichi x.x.x installed
✓ PySide6 (Qt 6.x.x) installed
✓ OpenCV x.x.x installed
✓ NumPy x.x.x installed
✓ Pillow installed

======================================================================
INSTALLATION COMPLETE
======================================================================

✓ Apple Silicon GPU acceleration enabled!
  ChromaCloud will use Metal Performance Shaders (MPS)
```

---

## Files Modified

The following files were updated to pin MediaPipe to 0.10.14:

1. **requirements_cc.txt** (Windows/Linux)
   - Changed: `mediapipe>=0.10.0` → `mediapipe==0.10.14`

2. **requirements_cc_macos.txt** (macOS)
   - Changed: `mediapipe>=0.10.0` → `mediapipe==0.10.14`

No code changes were required in Python files - the pinned version ensures the correct API is available.

---

## Future Considerations

### When to Upgrade MediaPipe?

Consider upgrading when:
1. MediaPipe 1.0+ is released with stable API
2. Significant new features are needed
3. Security vulnerabilities are found in 0.10.14
4. Community widely adopts new Task API

For now, **0.10.14 is the stable, proven choice** for ChromaCloud.

### Upgrading Path (Future)

If/when you decide to upgrade:
1. Update requirements to newer version
2. Implement version-compatible import (see MEDIAPIPE_VERSION_INVESTIGATION.md)
3. Test thoroughly on all platforms
4. Update documentation

---

## Summary

✅ **Requirements files updated** - MediaPipe pinned to 0.10.14  
✅ **macOS rebuild is straightforward** - Just delete cc_env and re-run install_cc.py  
✅ **Cross-platform consistency** - Same MediaPipe version everywhere  
✅ **No code changes needed** - Current code works perfectly with 0.10.14  

**Estimated rebuild time:** 3-5 minutes (depending on download speed)

🎉 **You're all set!** Just rebuild the macOS environment and ChromaCloud will work perfectly!
