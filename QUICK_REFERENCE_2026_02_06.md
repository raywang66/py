# Quick Reference - ChromaCloud Updates (Feb 6, 2026)

## ✅ What Was Fixed

### 1. 3D Visualization Title Correction
- **Before**: "3D HSL 圆柱楔形 (H: 15-25°)" ❌ 误导
- **After**: "3D HSL 圆柱楔形可视化" ✅ 准确
- **Reality**: Always displays ALL points, no hue filtering

### 2. Point Count Transparency
- **Before**: Always shows "50,000 个点已可视化" even if more points exist
- **After**: 
  - Shows "50,000 / 75,000 个点已可视化 (受限于最大点数)" when capped
  - Shows "30,000 个点已可视化" when below limit
- **Log**: Warns when points exceed limit

### 3. macOS Data Location
- **macOS**: `~/CC/chromacloud.db` and `~/CC/chromacloud.log`
- **Windows**: `<script_dir>/chromacloud.db` and `chromacloud.log` (unchanged)
- **Benefit**: Local storage when code is on SMB share

---

## 🎯 Key Points

### HSL Data Processing
```
Photo Analysis → ALL HSL points extracted → Statistics calculated on ALL points
                                          → 3D visualization shows ALL points*
                                             (*limited to first 50,000 for performance)
```

### No Filtering Anywhere
- ✅ Statistics: Uses ALL HSL points
- ✅ 3D Visualization: Tries to show ALL HSL points
- 🔧 Only limitation: GPU memory (default 50,000 max_points)

### Reference Lines
The yellow markers at 15° and 25° in 3D view are:
- ✅ Visual reference guides only
- ❌ NOT filtering boundaries
- Purpose: Help orient the cylinder view

---

## 🚀 For macOS Users

### Installation
```bash
# 1. Pull from GitHub
cd /path/to/your/ChromaCloud
git pull

# 2. Create virtual environment in ~/CC
python install_cc.py --venv ~/CC

# 3. Activate and install
source ~/CC/bin/activate
python install_cc.py

# 4. Run ChromaCloud
python CC_Main.py
```

### Data Files
```bash
# Check data directory
ls -la ~/CC/

# View log
tail -f ~/CC/chromacloud.log

# Check database
sqlite3 ~/CC/chromacloud.db ".tables"
```

---

## 📊 Performance Notes

### Current Limits
- Max points rendered: 50,000 (configurable in cc_config.py)
- Large faces may have 50,000+ points
- All points used for statistics
- Only first 50,000 shown in 3D

### To Increase Limit
Edit `cc_config.py`:
```python
class CC_RENDERER_CONFIG:
    max_points = 100000  # Increase to 100K
```

⚠️ Higher limits require more GPU memory

---

## 📝 Testing Checklist

- [ ] Large photo (>50K points) shows warning in log
- [ ] UI shows "X / Y 个点已可视化 (受限于最大点数)"
- [ ] Small photo (<50K points) shows "X 个点已可视化"
- [ ] macOS: Data files in ~/CC/
- [ ] Windows: Data files in script directory
- [ ] 3D view shows all hue ranges (not just 15-25°)
- [ ] Statistics calculate using all points

---

## 🐛 If Something Goes Wrong

### Check Log File
**Windows**: `C:\Users\rwang\lc_sln\py\chromacloud.log`
**macOS**: `~/CC/chromacloud.log`

Look for:
- "ChromaCloud data directory: ..."
- "Database: ..."
- "Uploading X points to 3D renderer"
- "Point cloud has X points, but renderer is limited to..."

### Common Issues
1. **3D view empty**: Check if Taichi is installed
2. **Performance slow**: Reduce max_points in cc_config.py
3. **Database locked**: Close other ChromaCloud instances
4. **macOS ~/CC not created**: Check permissions on home directory

---

## 📧 Summary for GitHub

**Commit Message:**
```
Fix 3D visualization clarity and add macOS data directory support

- Remove misleading hue range from 3D panel title
- Add point count transparency (total vs displayed)
- Log warnings when exceeding max_points limit
- Store data in ~/CC on macOS for SMB compatibility
```

**Modified Files:**
- CC_Main.py (data directory, UI labels)
- CC_Renderer3D.py (logging)
- New: MACOS_DATA_DIRECTORY_SETUP.md
- New: FIXES_SUMMARY_2026_02_06.md
