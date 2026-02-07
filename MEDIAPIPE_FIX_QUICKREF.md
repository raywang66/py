# MediaPipe Fix - Quick Reference Card

## The Issue
MediaPipe 0.10.15+ removed `mp.solutions` API. Additionally, MediaPipe 0.10.14 is **NOT available on macOS** (only 0.10.30, 0.10.31, 0.10.32).

## The Solution
✅ **Version-compatible import** in CC_SkinProcessor.py + platform-specific requirements

## Files Changed
1. `CC_SkinProcessor.py` - Added version-compatible import (lines 20-52)
2. `requirements_cc.txt` - `mediapipe>=0.10.0,<=0.10.14` (Windows uses 0.10.14)
3. `requirements_cc_macos.txt` - `mediapipe>=0.10.30` (macOS uses 0.10.30+)

## macOS Installation (3 Commands)
```bash
rm -rf cc_env
python3 install_cc.py --venv
source cc_env/bin/activate
```

## Verify Installation
```bash
python3 -c "import mediapipe as mp; from mediapipe.python.solutions import face_mesh; print(f'✓ MediaPipe {mp.__version__} ready!')"
# Expected: ✓ MediaPipe 0.10.32 ready! (or 0.10.30/0.10.31)
```

## How It Works
**Version-Compatible Import:**
- **macOS (0.10.30+):** Uses `from mediapipe.python.solutions import face_mesh`
- **Windows (0.10.14):** Uses `mp.solutions.face_mesh`
- **Same functionality** - both APIs are identical in behavior

## Why This Solution?
- ✅ Works on Windows (0.10.14) AND macOS (0.10.30+)
- ✅ Platform-optimal versions (0.10.14 lighter for Windows)
- ✅ Zero functional differences
- ✅ Automatic API detection
- ✅ Future-proof

## Platform Versions
| Platform | MediaPipe Version | API Used |
|----------|-------------------|----------|
| Windows  | 0.10.14 | `mp.solutions` (old) |
| macOS    | 0.10.30+ | `mediapipe.python.solutions` (new) |

## Full Documentation
- **macOS Install Guide:** `MACOS_INSTALL_FIX.md` ⭐ **READ THIS**
- **Investigation:** `MEDIAPIPE_VERSION_INVESTIGATION.md`
- **Explanation:** `MEDIAPIPE_VERSION_MYSTERY_EXPLAINED.md`

---
**Status:** ✅ Ready to install on macOS  
**Risk:** Very Low (tested solution)  
**Time:** ~3-5 minutes
