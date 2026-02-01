# ChromaCloud 文件夹自动扫描功能 - 使用指南

## 🎉 新功能已完成！

ChromaCloud 现在支持自动监控文件夹，实现无缝的 Lightroom 工作流集成。

## 📦 已实现的功能

### ✅ Phase 1: 基础功能
- [x] 数据库 Schema 扩展（支持 folder_path、auto_scan 字段）
- [x] CC_FolderWatcher 模块（文件夹扫描和监控）
- [x] CC_AutoAnalyzer 模块（自动分析队列）
- [x] UI: "Add Folder Album" 菜单项
- [x] UI: 自动显示分析结果（点击照片即可看到）

### ✅ Phase 2: 文件系统监控
- [x] watchdog 集成
- [x] 实时文件创建/修改/删除监控
- [x] 自动触发分析

### ✅ Phase 3: UI 增强
- [x] 状态栏分析进度显示
- [x] 文件夹 Album 视觉区分（📂 图标 + 🔄 标记）
- [x] 完整的分布统计显示（Lightness、Hue、Saturation）

## 🚀 如何使用

### 1. 启动 ChromaCloud

```bash
cd C:\Users\rwang\lc_sln\py
python CC_Main.py
```

### 2. 创建 Folder Album

**步骤：**
1. 点击菜单 `File → 📁 Add Folder Album...`
2. 选择要监控的文件夹（例如 Lightroom 的导出目录）
3. 在确认对话框中点击 "Yes"

**效果：**
- ChromaCloud 会扫描该文件夹及所有子文件夹
- 自动发现所有照片（JPG、PNG、RAW）
- 在后台自动分析所有照片
- 状态栏显示分析进度

### 3. 查看分析结果

**点击照片即可查看：**
- 左侧：照片缩略图列表
- 点击任意照片
- 右侧 "Analysis" 面板**自动显示**分析结果

**无需手动点击 "Analyze" 按钮！**

### 4. Lightroom 迭代工作流

**完美的迭代流程：**

```
1. Lightroom Classic:
   - 调整 HSL/Luminance/Orange: +15
   - Export → 导出到监控的文件夹

2. ChromaCloud（自动）:
   - 🔍 检测到新文件
   - ⚙️ 后台自动分析
   - ✅ 分析完成

3. 查看结果:
   - 点击照片
   - 右侧立即显示完整的分析结果
   - 查看 Lightness/Hue/Saturation 分布

4. 继续调整:
   - 根据数据返回 Lightroom
   - 修改参数
   - 重新导出（覆盖文件）
   - ChromaCloud 自动检测并重新分析
```

## 📊 分析结果显示

点击任意照片后，右侧 "Analysis" 面板显示：

### 基本信息
```
✓ Face detected! (from database)
12,345 points
Coverage: 45.2%
```

### 统计数据
```
Hue: 28.5° ± 5.2°
Sat: 42.3%
Light: 58.7%
```

### 📊 Lightness Distribution
```
Low  (<33%): 15.3%
Mid (33-67%): 62.1%
High (>67%): 22.6%
```

### 🎨 Hue Distribution
```
Very Red (0-10°): 5.2%
Red-Orange (10-25°): 38.5%
Normal (25-35°): 45.3%
Yellow (35-45°): 8.5%
Very Yellow (45-60°): 2.3%
Abnormal (>60°): 0.2%
```

### 💧 Saturation Distribution
```
Very Low (<15%): 8.2%
Low (15-30%): 22.5%
Normal (30-50%): 48.3%
High (50-70%): 18.5%
Very High (>70%): 2.5%
```

## 🎨 UI 元素说明

### 文件夹 Album 标识

在左侧导航栏中：

- **📂 Folder Album 🔄** - 自动监控的文件夹
- **📁 Normal Album** - 手动管理的相册

### 状态栏信息

分析过程中，状态栏会显示：

```
Scanning: IMG_1234.jpg (45%)
Auto-analyzing: 15/45 photos (33%)
Analysis complete: IMG_1234.jpg
```

## ⚙️ 技术细节

### 自动监控机制

**监控的事件：**
1. **文件创建** - 新照片自动添加并分析
2. **文件修改** - 照片修改后自动重新分析
3. **文件删除** - 从视图中移除（数据库保留记录）

### 支持的文件格式

- **JPG/JPEG** - ✅
- **PNG** - ✅
- **ARW** (Sony RAW) - ✅
- **NEF** (Nikon RAW) - ✅
- **CR2/CR3** (Canon RAW) - ✅
- **DNG** (Adobe RAW) - ✅

### 性能优化

- **后台队列** - 不阻塞 UI
- **增量分析** - 只分析新照片和修改过的照片
- **数据库缓存** - 避免重复分析

## 🔧 故障排除

### 问题 1: 文件夹扫描很慢

**原因：** 文件夹包含大量照片

**解决：**
- 正常现象，首次扫描需要时间
- 状态栏会显示进度
- 后续只分析新增/修改的照片

### 问题 2: 照片未自动分析

**检查：**
1. 确认文件夹 Album 有 🔄 标记
2. 查看状态栏是否显示分析进度
3. 检查照片格式是否支持
4. 查看日志文件（如果有错误）

### 问题 3: 照片修改后未更新

**解决：**
1. 确保文件系统监控正常运行
2. 尝试关闭并重新打开 ChromaCloud
3. 或手动点击 "Analyze" 按钮重新分析

## 📝 数据库变更

新增的数据库字段：

### albums 表
```sql
folder_path TEXT          -- 监控的文件夹路径
auto_scan INTEGER        -- 是否自动扫描 (0/1)
last_scan_time TIMESTAMP -- 最后扫描时间
```

### analysis_results 表
```sql
sat_very_low REAL    -- Saturation <15%
sat_low REAL         -- Saturation 15-30%
sat_normal REAL      -- Saturation 30-50%
sat_high REAL        -- Saturation 50-70%
sat_very_high REAL   -- Saturation >70%
```

**现有数据库会自动迁移，无需手动操作！**

## 🎯 实际应用案例

### 案例 1: Lightroom 肤色调整迭代

**场景：** 需要找到最佳的 Orange Luminance 值

**步骤：**

1. 在 ChromaCloud 中创建 Folder Album：`C:\LR_Exports\Skin_Test`

2. 在 Lightroom 中：
   - 原始照片，Orange Luminance: 0
   - Export → `Skin_Test\v1_baseline.jpg`
   
3. ChromaCloud 自动分析，查看结果：
   ```
   Lightness High: 18.2%
   ```
   
4. 返回 Lightroom：
   - Orange Luminance: +15
   - Export → `Skin_Test\v2_plus15.jpg`
   
5. ChromaCloud 自动分析：
   ```
   Lightness High: 24.5%  ← 提升了 6.3%
   ```
   
6. 继续测试：
   - Orange Luminance: +25
   - Export → `Skin_Test\v3_plus25.jpg`
   
7. 最终结果：
   ```
   Lightness High: 29.8%  ← 目标达成！
   ```

### 案例 2: 批量照片分析

**场景：** 拍摄了一组人像，想分析整体肤色分布

**步骤：**

1. 创建 Folder Album: `D:\Photos\Session_2024_01`

2. ChromaCloud 自动扫描并分析 45 张照片

3. 点击 "Statistics" 按钮查看整体分布

4. 发现整体 Lightness Low 过高（35%），说明整体偏暗

5. 在 Lightroom 中批量调整：
   - 选择所有照片
   - Orange Luminance: +18
   - 批量导出

6. ChromaCloud 自动重新分析所有照片

7. 查看统计结果，确认改善效果

## 🚀 未来计划

### 可能的增强功能

- [ ] 图形化柱状图（matplotlib/pyqtgraph）
- [ ] 分析历史记录（对比不同版本）
- [ ] 自动生成调整建议
- [ ] 多文件夹同时监控
- [ ] 云同步功能

## 💡 提示和技巧

### 提示 1: 组织你的导出文件夹

建议结构：
```
C:\LR_Exports\
├── Project_A\
│   ├── test_v1.jpg
│   ├── test_v2.jpg
│   └── test_v3.jpg
├── Project_B\
│   └── ...
└── Daily_Tests\
    └── ...
```

为每个项目创建一个 Folder Album。

### 提示 2: 命名规范

使用有意义的文件名：
```
portrait_baseline.jpg
portrait_orange_plus10.jpg
portrait_orange_plus20.jpg
portrait_final.jpg
```

这样更容易追踪调整历史。

### 提示 3: 利用 Statistics 功能

对于文件夹中的多个版本：
1. 点击 Album 右键 → "Statistics"
2. 查看所有版本的对比图表
3. 一目了然地看到调整趋势

## 📚 相关文档

- [Lightroom HSL 工作原理](LIGHTROOM_HSL_EXPLAINED.md)
- [ChromaCloud 技术文档](TECHNICAL_DETAILS_CC.md)
- [API 参考](API_REFERENCE_CC.md)

## ❓ 常见问题

**Q: Folder Album 和普通 Album 有什么区别？**

A: 
- Folder Album (📂 🔄): 自动监控文件夹，自动分析新照片
- Normal Album (📁): 手动添加照片，需要手动批量分析

**Q: 可以停止监控某个文件夹吗？**

A: 目前暂不支持，关闭 ChromaCloud 后监控会停止。下次打开会继续监控。

**Q: 数据库会变得很大吗？**

A: 每张照片的分析结果大约 1-2 KB，1000 张照片约 1-2 MB，不会很大。

**Q: 照片被删除后会怎样？**

A: 照片会从视图中移除，但数据库记录会保留，方便历史查询。

---

**享受全新的 ChromaCloud 自动工作流吧！** 🎨✨

如有问题或建议，请记录在项目文档中。

*文档创建日期：2026-02-01*  
*ChromaCloud v1.3 - Folder Auto-Scan Feature*
