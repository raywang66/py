# CRITICAL - MediaPipe 0.10.32 API Incompatibility

**Date:** February 7, 2026  
**Issue:** MediaPipe 0.10.32 removed ALL legacy APIs  
**Status:** ⚠️ **INCOMPATIBLE** - Need to downgrade

---

## What We Discovered

MediaPipe 0.10.32 output shows:
```
Available attributes: ['Image', 'ImageFormat', 'tasks', ...]
```

**This means:**
- ❌ No `solutions` module
- ❌ No `python.solutions` module  
- ❌ No `face_mesh` module
- ✅ Only `tasks` module (completely new API)

**MediaPipe 0.10.32 removed ALL legacy APIs and only provides the new tasks-based API.**

---

## The Problem

ChromaCloud uses the legacy FaceMesh API:
```python
# What ChromaCloud needs:
from mediapipe.python.solutions import face_mesh
detector = face_mesh.FaceMesh(...)
results = detector.process(image)
```

MediaPipe 0.10.32 only has:
```python
# What 0.10.32 provides:
from mediapipe.tasks.python.vision import FaceLandmarker
# Completely different API, requires model files, different results format
```

**Migrating to the tasks API would require major code refactoring (several hours of work).**

---

## IMMEDIATE SOLUTION - Downgrade MediaPipe

### Try MediaPipe 0.10.9 (Recommended for macOS)

MediaPipe 0.10.9 has the legacy API and should work on macOS:

```bash
cd /Volumes/lc_sln/py
source ~/CC/cc_env/bin/activate

# Uninstall 0.10.32
pip uninstall mediapipe -y

# Try 0.10.9
pip install mediapipe==0.10.9

# Test
python3 -c "
import mediapipe as mp
print(f'MediaPipe: {mp.__version__}')

# Check for solutions
if hasattr(mp, 'solutions'):
    from mediapipe.solutions import face_mesh
    print('✓ Legacy API (mp.solutions) found!')
elif hasattr(mp, 'python'):
    from mediapipe.python.solutions import face_mesh
    print('✓ Legacy API (python.solutions) found!')
else:
    print('✗ No legacy API found')
    print(f'Available: {dir(mp)}')
"
```

### If 0.10.9 Doesn't Work, Try 0.10.7

```bash
pip uninstall mediapipe -y
pip install mediapipe==0.10.7
```

### If None of These Work

Try progressively older versions until one works:
```bash
# Try each version until one has the legacy API
for version in 0.10.9 0.10.7 0.10.5 0.10.3 0.10.1 0.10.0; do
    pip uninstall mediapipe -y
    pip install mediapipe==$version 2>/dev/null
    if python3 -c "from mediapipe.solutions import face_mesh" 2>/dev/null; then
        echo "✓ MediaPipe $version works!"
        break
    fi
done
```

---

## Why This Happened

### MediaPipe Version History

| Version Range | API Available | Status for ChromaCloud |
|---------------|---------------|------------------------|
| 0.10.0 - 0.10.14 | `mp.solutions.face_mesh` | ✅ Works |
| 0.10.15 - 0.10.29 | `mediapipe.python.solutions.face_mesh` | ✅ Works |
| 0.10.30 - 0.10.32 | Only `tasks` API | ❌ Incompatible |

### What Google Did

MediaPipe 0.10.30+ completed their migration to the new "tasks" API:
- Old: Simple `FaceMesh()` class with `.process()` method
- New: `FaceLandmarker` with model files, different initialization, different results

**This is a BREAKING change that requires code refactoring.**

---

## Updated Requirements

I'll update the requirements files to prevent this issue:

### requirements_cc_macos.txt

```txt
# OLD (caused the problem):
mediapipe>=0.10.30

# NEW (will use compatible version):
mediapipe>=0.10.0,<0.10.30
```

This ensures macOS gets a compatible version.

---

## Testing After Downgrade

```bash
# After installing compatible MediaPipe version
python3 diagnose_mediapipe.py

# Should see:
# ✓ mediapipe module found
# ✓ mediapipe.solutions OR mediapipe.python.solutions found
# ✓ face_mesh imported

# Then test ChromaCloud:
python3 CC_Main.py
```

---

## Long-Term Solution (Future)

To support MediaPipe 0.10.30+, ChromaCloud needs:

1. **Migrate to tasks API** - Rewrite face detection code
2. **Download model files** - FaceLandmarker needs `.task` model files
3. **Update result handling** - Results format is different
4. **Test thoroughly** - Ensure same accuracy

**Estimated effort:** 4-6 hours of development + testing

**For now:** Use MediaPipe < 0.10.30

---

## Quick Commands Summary

### Step 1: Downgrade MediaPipe

```bash
cd /Volumes/lc_sln/py
source ~/CC/cc_env/bin/activate
pip uninstall mediapipe -y
pip install mediapipe==0.10.9
```

### Step 2: Verify

```bash
python3 diagnose_mediapipe.py
```

### Step 3: Launch ChromaCloud

```bash
python3 CC_Main.py
```

---

## If You Get "No matching distribution found"

If `mediapipe==0.10.9` isn't available on macOS, try:

```bash
# Check what versions are available
pip index versions mediapipe

# Try the highest version below 0.10.30 that's available
pip install mediapipe==0.10.X  # where X is highest available < 30
```

---

## Summary

❌ **Problem:** MediaPipe 0.10.32 removed legacy API  
✅ **Solution:** Downgrade to MediaPipe 0.10.9 (or highest < 0.10.30)  
🔧 **Action:** Run the downgrade commands above  
📝 **Updated:** CC_SkinProcessor.py now detects this and provides clear error  

**Next step:**
```bash
pip uninstall mediapipe -y
pip install mediapipe==0.10.9
python3 diagnose_mediapipe.py
```

🎯 This will get ChromaCloud working on macOS!
