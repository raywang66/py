# ChromaCloud Fixes Summary - February 6, 2026

## Issues Fixed

### 1. ✅ 3D HSL 圆柱楔形图 - 不再过滤超出15-25°范围的点

**问题描述：**
- 标题显示 "(H: 15-25°)" 误导用户以为只显示该范围的点
- 实际上代码中**从未过滤**，所有HSL点都被显示
- Statistics分布计算也已经不过滤了（之前已修复）

**修复内容：**
```python
# 修改前：
right_panel = QGroupBox("3D HSL 圆柱楔形 (H: 15-25°)")

# 修改后：
right_panel = QGroupBox("3D HSL 圆柱楔形可视化")
```

**结论：** 3D可视化一直都是显示全部点，没有任何过滤。现在标题也准确反映了这一点。

---

### 2. ✅ 50,000 点数上限 - 增加日志提示

**问题描述：**
- 大脸图片可能有超过50,000个HSL点
- 但3D渲染器限制最多显示50,000点
- 用户看到 "50,000个点已可视化" 不知道是否有更多点被截断

**修复内容：**

#### A. CC_Renderer3D.py - 添加日志警告
```python
def set_point_cloud(self, hsl_points: np.ndarray, color_mode: str = 'hsl'):
    import logging
    logger = logging.getLogger("CC_Renderer3D")
    
    total_points = len(hsl_points)
    n = min(total_points, self.max_points)
    
    if total_points > self.max_points:
        logger.warning(f"Point cloud has {total_points:,} points, but renderer is limited to {self.max_points:,} points. "
                     f"{total_points - self.max_points:,} points will not be displayed.")
    else:
        logger.info(f"Rendering {n:,} points")
```

**日志示例：**
```
# 如果有 75,000 个点：
WARNING [CC_Renderer3D] Point cloud has 75,000 points, but renderer is limited to 50,000 points. 25,000 points will not be displayed.

# 如果有 30,000 个点：
INFO [CC_Renderer3D] Rendering 30,000 points
```

#### B. CC_Main.py - UI显示总数和渲染数
```python
# 修改前：
controls_info = QLabel(
    f"{len(self.point_cloud):,} 个点已可视化\n"
    ...
)

# 修改后：
total_points = len(self.point_cloud)
displayed_points = min(total_points, self.renderer.max_points)

if total_points > displayed_points:
    points_info = f"{displayed_points:,} / {total_points:,} 个点已可视化 (受限于最大点数)"
else:
    points_info = f"{displayed_points:,} 个点已可视化"

controls_info = QLabel(
    f"{points_info}\n"
    ...
)
```

**UI效果：**
- 如果有 75,000 个点：显示 "50,000 / 75,000 个点已可视化 (受限于最大点数)"
- 如果有 30,000 个点：显示 "30,000 个点已可视化"

---

### 3. ✅ macOS数据目录配置

**问题描述：**
- 源代码在SMB共享上
- 数据库和日志应存储在本地以提高性能

**解决方案：**
```python
def get_data_directory():
    """Get platform-specific data directory for ChromaCloud files"""
    os_type = platform.system()
    
    if os_type == "Darwin":  # macOS
        # Use ~/CC for data files when running on macOS (SMB share friendly)
        data_dir = Path.home() / "CC"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    else:
        # Windows/Linux: use script directory
        return Path(__file__).parent

DATA_DIR = get_data_directory()
LOG_FILE = DATA_DIR / "chromacloud.log"
DB_FILE = DATA_DIR / "chromacloud.db"
```

**平台行为：**
- **macOS**: 数据存储在 `~/CC/`
  - `~/CC/chromacloud.db`
  - `~/CC/chromacloud.log`
- **Windows**: 数据存储在脚本目录（保持原样）
  - `C:\Users\rwang\lc_sln\py\chromacloud.db`
  - `C:\Users\rwang\lc_sln\py\chromacloud.log`

**启动日志会显示：**
```
INFO [CC_MainApp] ChromaCloud data directory: /Users/rwang/CC
INFO [CC_MainApp] Database: /Users/rwang/CC/chromacloud.db
INFO [CC_MainApp] Log file: /Users/rwang/CC/chromacloud.log
```

---

## 技术细节

### max_points 配置
50,000是默认值，可在 `cc_config.py` 中配置：
```python
class CC_RENDERER_CONFIG:
    max_points = 100000  # 增加到10万点
    point_size = 2.0
    background_color = (0.12, 0.12, 0.15)
```

### HSL统计计算
在 `CC_SkinProcessor.py` 中，统计计算**不过滤**任何点：
```python
# Line 229: Note: We do NOT filter by hue range here!
# 计算使用全部HSL点，包括超出15-25°范围的点
```

### 3D可视化
在 `CC_Renderer3D.py` 中：
- 接收全部HSL点
- 仅受 `max_points` 限制
- 显示所有色调、饱和度、亮度值
- 参考线（15°、20°、25°）仅作为视觉参考，不影响数据显示

---

## 测试建议

### 1. 测试大图片（>50,000点）
```python
# 加载大脸图片
# 观察日志输出：
# - CC_MainApp: "Uploading X points to 3D renderer"
# - CC_Renderer3D: "Point cloud has X points, but renderer is limited to 50,000 points..."
# - UI显示: "50,000 / X 个点已可视化 (受限于最大点数)"
```

### 2. 测试小图片（<50,000点）
```python
# 加载普通图片
# 观察日志输出：
# - CC_Renderer3D: "Rendering X points"
# - UI显示: "X 个点已可视化"
```

### 3. 测试macOS数据目录
```bash
# 在macOS上运行：
python CC_Main.py

# 检查数据目录：
ls -la ~/CC/
# 应该看到：
# chromacloud.db
# chromacloud.log
```

---

## 相关文件

- `CC_Main.py` - UI和数据目录配置
- `CC_Renderer3D.py` - 3D渲染器和点数限制
- `cc_config.py` - 配置参数（max_points）
- `CC_SkinProcessor.py` - HSL统计计算（无过滤）
- `MACOS_DATA_DIRECTORY_SETUP.md` - macOS配置详细说明

---

## Git Commit建议

```bash
git add CC_Main.py CC_Renderer3D.py MACOS_DATA_DIRECTORY_SETUP.md
git commit -m "Fix: 3D visualization clarity and macOS data directory

- Remove misleading '(H: 15-25°)' from 3D panel title (no filtering applied)
- Add logging when point cloud exceeds max_points limit (50,000)
- Show 'X / Y points' in UI when points are capped
- Store database and logs in ~/CC on macOS (SMB-friendly)
- Windows/Linux behavior unchanged (use script directory)"
```
