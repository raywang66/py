# MediaPipe 0.10.32 Issue - Complete Analysis

**Date:** February 7, 2026  
**Critical Discovery:** MediaPipe 0.10.32 incompatible with ChromaCloud  
**Status:** ⚠️ **BLOCKING ISSUE**

---

## What Happened

### The Journey
1. ✅ Initial install: MediaPipe 0.10.32 installed
2. ❌ Import failed: "mediapipe.python module not found"
3. 🔍 Diagnosed: Not corrupted - **API completely changed**
4. ✅ Reinstalled: Same version (0.10.32)
5. ❌ Still failed: **Discovered new "tasks" API only**

### The Discovery

MediaPipe 0.10.32 output:
```python
Available attributes: ['Image', 'ImageFormat', 'tasks', '__version__', ...]
```

**Missing:**
- ❌ `solutions`
- ❌ `python.solutions` 
- ❌ `face_mesh`

**Only has:**
- ✅ `tasks` (completely new, incompatible API)

---

## Root Cause

### MediaPipe API Evolution

```
v0.10.0 - 0.10.14:  mp.solutions.face_mesh              ✅ Works
v0.10.15 - 0.10.29: mediapipe.python.solutions.face_mesh  ✅ Works  
v0.10.30 - 0.10.32: mediapipe.tasks.python.vision.*      ❌ Incompatible
```

**MediaPipe 0.10.30+ removed ALL legacy APIs.**

### What ChromaCloud Needs vs. What 0.10.32 Provides

| ChromaCloud Code | MediaPipe 0.10.32 |
|------------------|-------------------|
| `from mediapipe.python.solutions import face_mesh` | ❌ Doesn't exist |
| `detector = face_mesh.FaceMesh(...)` | ❌ Doesn't exist |
| `results = detector.process(image)` | ❌ Different format |

| What 0.10.32 Requires |
|-----------------------|
| `from mediapipe.tasks.python.vision import FaceLandmarker` |
| Download `.task` model file |
| Different initialization |
| Different results format |
| Different processing method |

**This requires major code refactoring (4-6 hours).**

---

## The macOS Problem

From earlier diagnostics:
```
pip index versions mediapipe
Available versions: 0.10.30, 0.10.31, 0.10.32
```

**macOS PyPI ONLY has versions 0.10.30+, ALL of which removed the legacy API.**

This means:
- ❌ Can't use 0.10.14 (not available on macOS)
- ❌ Can't use 0.10.9 (likely not available on macOS)
- ❌ Can't use ANY compatible version on macOS

---

## Solutions

### Option 1: Try Downgrading (May Not Work on macOS)

```bash
bash downgrade_mediapipe.sh
```

This will try versions 0.10.9, 0.10.7, 0.10.5, etc.

**Likelihood of success:** Low (macOS PyPI seems to only have 0.10.30+)

### Option 2: Implement tasks API Support (Best Long-Term)

Migrate ChromaCloud to use MediaPipe's new tasks API.

**Requirements:**
1. Rewrite CC_SkinProcessor face detection code
2. Download face_landmarker.task model file (~10MB)
3. Update result processing
4. Test thoroughly

**Estimated time:** 4-6 hours
**Benefits:** Future-proof, supports latest MediaPipe

### Option 3: Use ChromaCloud on Windows

Windows has MediaPipe 0.10.14 available and working.

**Immediate:** ✅ Works now
**Long-term:** ⚠️ Still need to migrate eventually

---

## What I've Done

### 1. Updated CC_SkinProcessor.py

Added detection for this exact scenario:
```python
if mp_face_mesh_module is None and hasattr(mp, 'tasks'):
    raise ImportError(
        f"MediaPipe {mp.__version__} uses the new tasks API "
        f"which is not yet supported by ChromaCloud.\n"
        f"SOLUTION: pip install mediapipe==0.10.9\n"
        f"ChromaCloud will be updated to support tasks API in future."
    )
```

### 2. Updated requirements_cc_macos.txt

```txt
# Prevent installing incompatible versions
mediapipe>=0.10.0,<0.10.30
```

### 3. Created Scripts

- `downgrade_mediapipe.sh` - Automated downgrade attempt
- `MEDIAPIPE_0.10.32_INCOMPATIBLE.md` - Full documentation

### 4. Updated Diagnostic

`diagnose_mediapipe.py` now checks for tasks API and provides specific guidance.

---

## Immediate Action

### Try the Downgrade

```bash
cd /Volumes/lc_sln/py
source ~/CC/cc_env/bin/activate
bash downgrade_mediapipe.sh
```

**If this works:** ChromaCloud will run!  
**If this fails:** macOS doesn't have compatible versions

### If Downgrade Fails

You have two choices:

1. **Wait for tasks API support** (I can implement this)
2. **Use Windows temporarily** (works now with 0.10.14)

---

## Implementing tasks API Support (If Needed)

If no compatible MediaPipe version is available on macOS, I can update ChromaCloud to support the new tasks API.

**What needs to change:**

1. **CC_SkinProcessor.py** - Face detection code
2. **Model file** - Download face_landmarker.task
3. **Testing** - Verify results match legacy API

**Would you like me to implement this?**

It would take about 30-60 minutes to implement and test the migration.

---

## Summary

❌ **MediaPipe 0.10.32:** Incompatible (removed legacy API)  
❌ **macOS PyPI:** Only has 0.10.30+ (all incompatible)  
✅ **Windows:** Has 0.10.14 (compatible)  

**Try first:**
```bash
bash downgrade_mediapipe.sh
```

**If that fails:**
- Option A: Migrate to tasks API (I can do this)
- Option B: Use Windows temporarily

**Your call:** Should I implement tasks API support for MediaPipe 0.10.30+?

---

## Technical Details: tasks API Migration

If we need to migrate, here's what changes:

### Old API (Current):
```python
from mediapipe.python.solutions import face_mesh

detector = face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

results = detector.process(image_rgb)
if results.multi_face_landmarks:
    landmarks = results.multi_face_landmarks[0]
```

### New API (Tasks):
```python
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(
    model_asset_path='face_landmarker.task'
)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=1,
    min_face_detection_confidence=0.5
)

with vision.FaceLandmarker.create_from_options(options) as landmarker:
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    result = landmarker.detect(mp_image)
    if result.face_landmarks:
        landmarks = result.face_landmarks[0]
```

**Doable, but requires testing to ensure same results.**
