# MediaPipe "Cannot Be Found" Error - Troubleshooting Guide

**Issue:** MediaPipe 0.10.32 is installed (`pip show mediapipe` confirms), but import fails  
**Status:** Diagnostic needed

---

## Quick Diagnostic

Run this on your macOS machine:

```bash
cd /Volumes/lc_sln/py
source ~/CC/cc_env/bin/activate
python3 diagnose_mediapipe.py
```

This will show exactly where the import is failing.

---

## Common Causes & Solutions

### 1. Wrong Python Environment ⚠️

**Problem:** Using system Python instead of virtual environment Python

**Check:**
```bash
which python3
# Should show: /Users/test/CC/cc_env/bin/python3

pip show mediapipe
# Should show: Location: /Users/test/CC/cc_env/lib/python3.13/site-packages
```

**Solution:**
```bash
source ~/CC/cc_env/bin/activate
```

### 2. Import from Wrong Directory ⚠️

**Problem:** Running Python from a directory where CC_SkinProcessor.py doesn't exist

**Check:**
```bash
pwd
# Should be: /Volumes/lc_sln/py

ls CC_SkinProcessor.py
# Should show: CC_SkinProcessor.py
```

**Solution:**
```bash
cd /Volumes/lc_sln/py
python3 CC_Main.py
```

### 3. MediaPipe Package Corruption ⚠️

**Problem:** MediaPipe installed but submodules missing

**Check:**
```bash
python3 -c "from mediapipe.python.solutions import face_mesh; print('OK')"
```

**If this fails, reinstall:**
```bash
pip uninstall mediapipe -y
pip install mediapipe>=0.10.30
```

### 4. Python Path Issue ⚠️

**Problem:** `sys.path` doesn't include current directory

**Check:**
```bash
python3 -c "import sys; print('\n'.join(sys.path))"
```

**Workaround:**
```bash
# Run from correct directory
cd /Volumes/lc_sln/py
python3 CC_Main.py

# Or set PYTHONPATH
export PYTHONPATH=/Volumes/lc_sln/py:$PYTHONPATH
python3 CC_Main.py
```

### 5. Cached .pyc Files ⚠️

**Problem:** Old compiled Python files causing import issues

**Solution:**
```bash
cd /Volumes/lc_sln/py
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
python3 CC_Main.py
```

---

## Step-by-Step Diagnostic

### Step 1: Verify Virtual Environment

```bash
# Activate venv
source ~/CC/cc_env/bin/activate

# Check Python location
which python3
# Expected: /Users/test/CC/cc_env/bin/python3

# Check pip location  
which pip
# Expected: /Users/test/CC/cc_env/bin/pip

# Verify MediaPipe in venv
pip show mediapipe
# Should show: Version: 0.10.32
#              Location: /Users/test/CC/cc_env/lib/python3.13/site-packages
```

### Step 2: Test MediaPipe Import Directly

```bash
python3 -c "
import mediapipe as mp
print(f'✓ MediaPipe {mp.__version__} imported')

from mediapipe.python.solutions import face_mesh
print('✓ face_mesh imported')

fm = face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)
print('✓ FaceMesh instantiated')
print('✅ MediaPipe working!')
"
```

**If this works:** MediaPipe is fine, issue is with CC_SkinProcessor import

**If this fails:** MediaPipe installation issue

### Step 3: Test CC_SkinProcessor Import

```bash
cd /Volumes/lc_sln/py

python3 -c "
import sys
print('Current directory:', sys.path[0])
print('Trying to import CC_SkinProcessor...')

from CC_SkinProcessor import MEDIAPIPE_AVAILABLE, MEDIAPIPE_API
print(f'✓ MEDIAPIPE_AVAILABLE: {MEDIAPIPE_AVAILABLE}')
print(f'✓ MEDIAPIPE_API: {MEDIAPIPE_API}')
print('✅ CC_SkinProcessor imported successfully!')
"
```

**If this fails:** Check the exact error message

### Step 4: Run Diagnostic Script

```bash
python3 diagnose_mediapipe.py
```

This comprehensive script will pinpoint the exact issue.

---

## Detailed Error Analysis

### Error Type 1: "No module named 'mediapipe'"

**Cause:** MediaPipe not installed in current Python environment

**Solution:**
```bash
source ~/CC/cc_env/bin/activate
pip install mediapipe>=0.10.30
```

### Error Type 2: "No module named 'mediapipe.python'"

**Cause:** MediaPipe package corrupted or wrong version

**Solution:**
```bash
pip uninstall mediapipe -y
pip cache purge
pip install mediapipe==0.10.32
```

### Error Type 3: "cannot import name 'face_mesh'"

**Cause:** MediaPipe version issue

**Check version:**
```bash
python3 -c "import mediapipe; print(mediapipe.__version__)"
```

**Must be 0.10.30 or higher for macOS**

### Error Type 4: "No module named 'CC_SkinProcessor'"

**Cause:** Wrong working directory

**Solution:**
```bash
cd /Volumes/lc_sln/py
python3 CC_Main.py
```

---

## What to Report

If the diagnostic script fails, please provide:

1. **Output of diagnostic script:**
   ```bash
   python3 diagnose_mediapipe.py > diagnosis.txt 2>&1
   ```

2. **Environment info:**
   ```bash
   which python3
   pip show mediapipe
   python3 --version
   ```

3. **Exact error message:**
   ```bash
   python3 CC_Main.py 2>&1 | head -30
   ```

---

## Quick Fix Checklist

Try these in order:

- [ ] 1. Activate virtual environment: `source ~/CC/cc_env/bin/activate`
- [ ] 2. Navigate to project: `cd /Volumes/lc_sln/py`
- [ ] 3. Verify MediaPipe: `pip show mediapipe` (should be 0.10.32)
- [ ] 4. Test import: `python3 diagnose_mediapipe.py`
- [ ] 5. Clear cache: `find . -name "*.pyc" -delete`
- [ ] 6. Reinstall MediaPipe: `pip uninstall mediapipe -y && pip install mediapipe>=0.10.30`
- [ ] 7. Try running: `python3 CC_Main.py`

---

## Expected Working State

When everything works correctly, you should see:

```bash
$ source ~/CC/cc_env/bin/activate
(cc_env) $ cd /Volumes/lc_sln/py
(cc_env) $ python3 diagnose_mediapipe.py

======================================================================
MediaPipe Import Diagnostics
======================================================================
Python executable: /Users/test/CC/cc_env/bin/python3
Python version: 3.13.10
...

Step 1: Checking if mediapipe package exists...
✓ mediapipe module found
  Location: /Users/test/CC/cc_env/lib/python3.13/site-packages/mediapipe/__init__.py
  Version: 0.10.32

Step 2: Checking mediapipe.python module...
✓ mediapipe.python module found

Step 3: Checking mediapipe.python.solutions module...
✓ mediapipe.python.solutions module found

Step 4: Checking face_mesh module...
✓ face_mesh module imported successfully

Step 5: Testing FaceMesh instantiation...
✓ FaceMesh detector created successfully

Step 6: Checking old API (mp.solutions)...
✓ Old API not present (correct for 0.10.30+)

======================================================================
✅ ALL CHECKS PASSED!
======================================================================
```

---

## Still Not Working?

If after all diagnostics MediaPipe still "cannot be found":

### Nuclear Option: Full Reinstall

```bash
# Remove everything
rm -rf ~/CC/cc_env

# Rebuild from scratch
cd /Volumes/lc_sln/py
python3 install_cc.py --venv

# Activate new environment
source ~/CC/cc_env/bin/activate

# Verify
python3 diagnose_mediapipe.py

# Run ChromaCloud
python3 CC_Main.py
```

This will create a completely fresh installation.

---

## Summary

The error "MediaPipe cannot be found" despite `pip show mediapipe` working usually means:

1. **Most likely:** Wrong Python environment (not using venv)
2. **Second most likely:** Wrong working directory
3. **Less likely:** Package corruption
4. **Rare:** Python path configuration issue

**Run the diagnostic script first:**
```bash
cd /Volumes/lc_sln/py
source ~/CC/cc_env/bin/activate
python3 diagnose_mediapipe.py
```

This will tell us exactly what's wrong! 🔍
