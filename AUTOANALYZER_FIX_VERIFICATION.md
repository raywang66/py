# AutoAnalyzer 修复 - 快速验证指南

## 问题
FolderWatcher 发现的新照片，AutoAnalyzer 分析结果不正确（没有正确提取面部遮罩）。

## 修复
为 AutoAnalyzer 线程创建独立的 CC_SkinProcessor 实例（MediaPipe 不是线程安全的）。

## 验证步骤

### 1. 删除旧数据库（可选）
如果想重新分析已有照片：
```powershell
Remove-Item C:\Users\rwang\lc_sln\py\chromacloud.db
```

### 2. 运行 ChromaCloud
```powershell
cd C:\Users\rwang\lc_sln\py
.\start_chromacloud.bat
```

### 3. 创建 Folder Album
1. 右键点击 "Folders" → "Add Folder"
2. 选择包含照片的文件夹
3. FolderWatcher 会自动扫描并添加照片到队列

### 4. 查看日志
检查 `chromacloud.log` 应该看到：

```
[AutoAnalyzer] ✅ Created thread-local CC_SkinProcessor (MediaPipe face detection enabled)
[AutoAnalyzer] 🔍 Analyzing: photo.jpg
[AutoAnalyzer]   Image loaded: (3456, 2304, 3)
[AutoAnalyzer]   Face mask coverage: 8.52%
[AutoAnalyzer]   Skin pixels extracted: 12847
[AutoAnalyzer] ✅ Analysis complete: photo.jpg
[AutoAnalyzer]   Hue mean: 0.05, Saturation: 0.33
```

关键指标：
- ✅ **Face mask coverage > 0%** - 说明面部检测成功
- ✅ **Skin pixels > 0** - 说明提取了面部像素
- ✅ **Hue mean 在 [0.03, 0.08]** - 正常肤色范围

### 5. 对比验证
选择一张由 AutoAnalyzer 分析的照片：
1. 点击照片缩略图（右侧显示分析结果）
2. 点击 "🔍 Analyze" 按钮（重新分析）
3. 对比两次的结果：
   - Hue mean 应该相同
   - Saturation 应该相同
   - Lightness 应该相同

如果结果一致 → ✅ 修复成功！

## 预期结果

修复后：
- ✅ AutoAnalyzer 正确检测面部
- ✅ 提取面部肤色遮罩
- ✅ 计算的 HSL 统计数据准确
- ✅ 与 Analyze 按钮结果完全一致

## 技术细节

**问题根源**: MediaPipe FaceMesh 不是线程安全的
**解决方案**: 每个线程创建独立的 processor 实例
**文件修改**: CC_AutoAnalyzer.py (3 处修改)

详细说明见: `AUTOANALYZER_FIX_COMPLETE.md`
