# 🎨 ChromaCloud v1.2 - Folder Auto-Scan with Tree Structure

完美集成 Lightroom Classic 的肤色分析工具，支持自动文件夹监控和树状目录结构！

## ✨ 新功能亮点（v1.2）

### 🌲 真正的树状目录结构（v1.2）

- ✅ 递归显示所有子目录
- ✅ 支持展开/折叠查看
- ✅ 每个子文件夹显示照片数量
- ✅ 点击子文件夹筛选照片
- ✅ 支持无限层级（默认最多10层）
- 📚 详见 [DIRECTORY_TREE_FEATURE.md](DIRECTORY_TREE_FEATURE.md)

**示例结构：**
```
📂 Folders (1)
  └─ 📂 My_Photos (156)
     ├─ 📁 January (45)
     ├─ 📁 February (67)
     └─ 📁 March (44)
        └─ 📁 Studio (20)
```

### 🐛 线程安全修复（v1.1.1）

- ✅ 修复了 SQLite 线程安全错误
- ✅ 每个线程使用独立的数据库连接
- ✅ 优化了资源管理和连接生命周期
- 📚 详见 [THREAD_SAFETY_FIX_v1.1.1.md](THREAD_SAFETY_FIX_v1.1.1.md)

### 📂 Folders vs 📁 Albums （v1.1）

```
📷 All Photos
│
📂 Folders (自动监控)
├─ 📂 Lightroom_Exports (45)    ← 自动扫描、自动分析
└─ 📂 Studio_Photos (123)
│
📁 Albums (手动管理)
├─ 📁 Best Portraits (25)       ← 虚拟集合
└─ 📁 Client Work (67)
```

### 🚀 工作流革命

**之前：** Lightroom → Export → ChromaCloud → 添加 → 批量分析 → 等待 → 查看  
**现在：** Lightroom → Export → **自动完成** → 点击查看！

## 🎯 快速开始

### 1. 启动

```bash
# 方式1: 双击
start_chromacloud.bat

# 方式2: 命令行
python CC_Main.py
```

### 2. 创建 Folder Album

```
File → 📁 Add Folder Album...
→ 选择 Lightroom 导出目录
→ 确认
```

### 3. 开始工作

```
Lightroom:
  调整 HSL → Export

ChromaCloud:
  自动检测 → 自动分析 → 点击查看！
```

## 📊 功能特性

### ✅ 自动化

- [x] 自动扫描文件夹及子目录
- [x] 自动检测新增/修改的照片
- [x] 后台自动分析（不阻塞UI）
- [x] 启动时自动恢复监控

### ✅ 完整分析

点击照片后自动显示：

```
✓ Face detected! (12,345 points)

📊 Lightness Distribution
  Low/Mid/High 百分比

🎨 Hue Distribution
  6个范围的详细分布

💧 Saturation Distribution
  5个范围的详细分布
```

### ✅ 清晰的UI

- 📂 Folders（自动监控）和 📁 Albums（手动管理）分离
- 树状结构支持展开/折叠
- 状态栏实时显示进度
- Tooltip 显示完整路径

## 🧪 测试验证

```bash
# 功能测试
python test_folder_autoscan.py

# 调试测试
python test_debug_folder_scan.py

# 线程安全测试（v1.1.1+）
python test_thread_safety.py
```

预期结果：
```
✓ All tests passed!
✓ Watcher successfully emitted X photos
✓ Scan complete signal received
✓ Thread safety test PASSED
```

## 📚 文档

| 文档 | 说明 |
|------|------|
| [DIRECTORY_TREE_FEATURE.md](DIRECTORY_TREE_FEATURE.md) | 🌲 树状目录结构 |
| [TREE_STRUCTURE_COMPLETE.md](TREE_STRUCTURE_COMPLETE.md) | 📋 树状结构实现总结 |
| [THREAD_SAFETY_FIX_v1.1.1.md](THREAD_SAFETY_FIX_v1.1.1.md) | 🐛 线程安全修复 |
| [FINAL_SUMMARY.md](FINAL_SUMMARY.md) | 📋 完成总结 |
| [CHANGELOG_v1.1.md](CHANGELOG_v1.1.md) | 📝 更新日志 |
| [QUICKSTART_FOLDER_AUTOSCAN.md](QUICKSTART_FOLDER_AUTOSCAN.md) | 🚀 快速开始 |
| [FOLDER_AUTO_SCAN_USAGE_GUIDE.md](FOLDER_AUTO_SCAN_USAGE_GUIDE.md) | 📖 详细指南 |
| [FOLDER_AUTO_SCAN_FEATURE.md](FOLDER_AUTO_SCAN_FEATURE.md) | 🏗️ 设计文档 |
| [LIGHTROOM_HSL_EXPLAINED.md](LIGHTROOM_HSL_EXPLAINED.md) | 💡 HSL 原理 |

## 🔧 技术架构

```
CC_Main.py (主程序)
├── CC_FolderWatcher.py (文件夹监控)
├── CC_AutoAnalyzer.py (自动分析队列)
├── CC_Database.py (数据库)
├── CC_SkinProcessor.py (面部分析)
└── CC_Renderer3D.py (3D可视化)
```

## 💡 使用场景

### Scenario 1: Lightroom 肤色调整

```
1. 在 Lightroom 调整 Orange Luminance
2. Export 到监控的文件夹
3. ChromaCloud 自动分析
4. 点击查看 Lightness High 是否达标
5. 继续调整直到满意
```

### Scenario 2: 批量照片分析

```
1. 创建 Folder Album 指向拍摄目录
2. ChromaCloud 自动扫描所有照片
3. 后台自动分析
4. 逐个查看或查看统计
```

## 🐛 故障排除

### 照片不显示？

检查：
1. 左侧是否有 🔄 标记（表示监控中）
2. 状态栏是否显示分析进度
3. Console 是否有错误日志

### 监控不工作？

检查：
1. 文件夹路径是否正确
2. 是否有读取权限
3. 重启 ChromaCloud

## 📦 依赖

```bash
pip install -r requirements_cc.txt
```

核心依赖：
- PySide6 (UI)
- mediapipe (面部检测)
- watchdog (文件监控) ← 新增
- numpy, opencv-python, Pillow

## 🎊 更新日志

### v1.2 (2026-02-01) - 树状目录结构

✅ **递归显示子目录树**  
✅ 支持展开/折叠查看子文件夹  
✅ 每个子文件夹显示照片数量  
✅ 点击子文件夹筛选查看照片  
✅ 智能过滤空文件夹  
✅ 支持无限层级（默认最多10层）

### v1.1.1 (2026-02-01) - 线程安全修复

✅ **修复 SQLite 线程安全错误**  
✅ 每个线程创建独立的数据库连接  
✅ 优化连接生命周期管理  
✅ 添加线程安全验证测试

### v1.1 (2026-02-01) - Folder Auto-Scan

✅ 修复照片扫描后不显示的问题  
✅ Folders 和 Albums 分离显示  
✅ 树状结构支持展开/折叠  
✅ 启动时自动恢复监控  
✅ 改进的删除功能  
✅ 完整的测试验证

## 🚀 开始使用

```bash
# 1. 启动
start_chromacloud.bat

# 2. 创建 Folder Album
File → Add Folder Album → 选择文件夹

# 3. 开始分析！
```

**享受全新的工作流吧！** 🎉✨

---

**版本**: v1.2  
**日期**: 2026-02-01  
**状态**: ✅ 生产就绪（支持树状结构）  
**作者**: Senior Software Architect
