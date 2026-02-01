# 🚀 ChromaCloud 文件夹自动扫描 - 快速启动指南

## ⚡ 5 分钟上手

### 第 1 步：启动 ChromaCloud

```bash
cd C:\Users\rwang\lc_sln\py
python CC_Main.py
```

### 第 2 步：创建 Folder Album

1. 点击菜单：**File → 📁 Add Folder Album...**
2. 选择你的 Lightroom 导出文件夹
3. 点击 **Yes** 确认

**就这么简单！** ChromaCloud 会自动：
- 🔍 扫描所有照片
- ⚙️ 后台分析
- 📊 保存结果到数据库

### 第 3 步：查看结果

1. 左侧点击任意照片
2. 右侧 **立即显示** 完整分析结果
3. 无需等待，无需点击 "Analyze"！

## 📋 完整的分析数据

点击照片后，你会看到：

```
✓ Face detected! (from database)
12,345 points
Coverage: 45.2%

Hue: 28.5° ± 5.2°
Sat: 42.3%
Light: 58.7%

📊 Lightness Distribution:
  Low  (<33%): 15.3%
  Mid (33-67%): 62.1%
  High (>67%): 22.6%

🎨 Hue Distribution:
  Very Red (0-10°): 5.2%
  Red-Orange (10-25°): 38.5%
  Normal (25-35°): 45.3%
  Yellow (35-45°): 8.5%
  Very Yellow (45-60°): 2.3%
  Abnormal (>60°): 0.2%

💧 Saturation Distribution:
  Very Low (<15%): 8.2%
  Low (15-30%): 22.5%
  Normal (30-50%): 48.3%
  High (50-70%): 18.5%
  Very High (>70%): 2.5%
```

## 🎨 Lightroom 迭代工作流

### 典型场景：调整肤色亮度

**目标：** 提升 Lightness High 的比例

1. **Lightroom**:
   - Orange Luminance: +15
   - Export → `test_v1.jpg`

2. **ChromaCloud**（自动）:
   - 检测到新文件
   - 后台分析
   - ✅ 完成

3. **查看结果**:
   - 点击 `test_v1.jpg`
   - 查看 Lightness High: 22.6%

4. **继续调整**:
   - 返回 Lightroom
   - Orange Luminance: +25
   - Export → `test_v2.jpg`（或覆盖 v1）

5. **再次查看**:
   - 点击 `test_v2.jpg`
   - 查看 Lightness High: 29.8% ← 提升了！

**完美的迭代循环！** 🎉

## 🔄 自动监控

Folder Album 会**实时监控**文件变化：

- ➕ **新文件** → 自动添加并分析
- ✏️ **修改文件** → 自动重新分析
- ➖ **删除文件** → 自动从列表移除

**你只需要在 Lightroom 中 Export，其他的交给 ChromaCloud！**

## 💡 实用技巧

### 技巧 1: 文件命名

建议使用有意义的名称：

```
portrait_baseline.jpg
portrait_orange_15.jpg
portrait_orange_25.jpg
portrait_final.jpg
```

### 技巧 2: 批量对比

1. 导出多个版本到同一个 Folder Album
2. 点击 Album 右键 → **Statistics**
3. 查看所有版本的对比图表

### 技巧 3: 文件夹组织

```
C:\LR_Exports\
├── Skin_Tests\        ← Folder Album 1
│   ├── test_v1.jpg
│   ├── test_v2.jpg
│   └── test_v3.jpg
├── Project_A\         ← Folder Album 2
│   └── ...
└── Daily_Work\        ← Folder Album 3
    └── ...
```

每个项目一个 Folder Album！

## 🎯 识别 Folder Album

在左侧导航栏中：

- **📂 Folder Album 🔄** ← 自动监控
- **📁 Normal Album** ← 手动管理

## 📊 状态栏信息

扫描和分析时，底部状态栏显示：

```
Scanning: IMG_1234.jpg (45%)
Auto-analyzing: 15/45 photos (33%)
Analysis complete: IMG_1234.jpg
```

## ❓ 常见问题

**Q: 扫描很慢？**  
A: 首次扫描大量照片需要时间，之后只处理新增/修改的照片。

**Q: 照片没有自动分析？**  
A: 检查 Album 是否有 🔄 标记，查看状态栏是否显示进度。

**Q: 可以停止监控吗？**  
A: 关闭 ChromaCloud 即停止监控，下次打开会继续。

## 📚 更多文档

- **详细使用指南**: `FOLDER_AUTO_SCAN_USAGE_GUIDE.md`
- **设计文档**: `FOLDER_AUTO_SCAN_FEATURE.md`
- **Lightroom HSL 原理**: `LIGHTROOM_HSL_EXPLAINED.md`
- **实现报告**: `IMPLEMENTATION_COMPLETE.md`

## 🎊 享受新工作流！

**从繁琐到流畅，只需要一个 Folder Album！** 🚀✨

---

*快速启动指南 v1.0*  
*ChromaCloud v1.3 - Folder Auto-Scan Feature*
