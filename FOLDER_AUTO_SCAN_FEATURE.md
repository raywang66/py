# ChromaCloud 文件夹自动扫描功能设计文档

## 概述

为 ChromaCloud 添加类似 Obsidian 的文件夹监控功能，实现自动扫描、分析和管理照片的完整工作流。

## 🎯 核心需求

### 1. 自动扫描目录
- 监控指定目录及所有子目录
- 自动发现新增的照片文件
- 支持多种图片格式（JPG, PNG, RAW）

### 2. 自动分析
- 新照片自动触发面部肤色分析
- 后台处理，不阻塞 UI
- 分析结果自动保存到数据库

### 3. 即时预览
- 点击任意照片，右侧 "Analysis" 面板自动显示分析结果
- 显示三个柱状图：Lightness、Hue、Saturation 分布
- 无需手动点击 "Analyze" 按钮

### 4. 文件系统监控
- 实时监控文件系统变化
- 新增照片自动感知并分析
- 删除照片自动更新数据库

## 🏗️ 架构设计

### 现有架构分析

**当前 ChromaCloud 架构：**
```
CC_Main.py (MainWindow)
├── CC_Database.py (数据库管理)
├── CC_SkinProcessor.py (面部分析)
├── CC_Renderer3D.py (3D 可视化)
└── CC_StatisticsWindow.py (统计窗口)
```

**现有功能流程：**
1. 用户创建 Album
2. 手动添加照片到 Album（通过文件对话框选择）
3. 照片被复制到 `Photos/` 目录
4. 用户点击 "Batch Analyze" 批量分析
5. 分析结果保存到数据库

**存在的问题：**
- 需要手动选择文件
- 需要手动触发批量分析
- 从 Lightroom 导出后需要重新导入
- 迭代工作流繁琐

### 新增架构

```
CC_Main.py (MainWindow)
├── CC_Database.py (数据库管理)
├── CC_SkinProcessor.py (面部分析)
├── CC_Renderer3D.py (3D 可视化)
├── CC_StatisticsWindow.py (统计窗口)
└── 🆕 CC_FolderWatcher.py (文件夹监控)
    ├── 文件系统监控 (watchdog)
    ├── 自动扫描线程
    └── 自动分析队列
```

## 📦 实现方案

### 方案 A：文件夹作为 Album（推荐）

**核心思想：** 
- 一个文件夹 = 一个 Album
- 自动监控文件夹，动态同步照片
- 保持现有 Album 系统，增强其功能

**优势：**
- 与现有架构完美融合
- 复用现有的 Album 管理功能
- 数据库结构无需大改
- 用户界面变化最小

**实现步骤：**

#### 1. 扩展数据库 Schema

```sql
-- 为 albums 表添加 folder_path 字段
ALTER TABLE albums ADD COLUMN folder_path TEXT;
ALTER TABLE albums ADD COLUMN auto_scan INTEGER DEFAULT 0;
ALTER TABLE albums ADD COLUMN last_scan_time TIMESTAMP;

-- 索引优化
CREATE INDEX idx_albums_folder ON albums(folder_path);
```

#### 2. 创建 CC_FolderWatcher 类

```python
# CC_FolderWatcher.py
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QThread, Signal

class CC_FolderWatcher(QThread):
    """文件夹监控线程，自动发现新照片"""
    
    # 信号
    new_photos_found = Signal(list)  # 发现新照片
    photos_removed = Signal(list)    # 照片被删除
    scan_progress = Signal(int, str) # 扫描进度
    
    def __init__(self, folder_path: Path, db: CC_Database):
        super().__init__()
        self.folder_path = folder_path
        self.db = db
        self.observer = None
        self.known_photos: Set[Path] = set()
        
    def initial_scan(self):
        """初始扫描：发现所有现有照片"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.nef', '.cr2', '.cr3', '.dng'}
        all_photos = []
        
        for ext in image_extensions:
            all_photos.extend(self.folder_path.rglob(f'*{ext}'))
            all_photos.extend(self.folder_path.rglob(f'*{ext.upper()}'))
        
        self.known_photos = set(all_photos)
        return all_photos
    
    def start_watching(self):
        """开始监控文件系统"""
        event_handler = FolderEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.folder_path), recursive=True)
        self.observer.start()
    
    def stop_watching(self):
        """停止监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

class FolderEventHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, watcher: CC_FolderWatcher):
        self.watcher = watcher
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            path = Path(event.src_path)
            if self._is_image(path):
                self.watcher.new_photos_found.emit([path])
    
    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            path = Path(event.src_path)
            if self._is_image(path):
                self.watcher.photos_removed.emit([path])
    
    def _is_image(self, path: Path) -> bool:
        ext = path.suffix.lower()
        return ext in {'.jpg', '.jpeg', '.png', '.arw', '.nef', '.cr2', '.cr3', '.dng'}
```

#### 3. 创建自动分析队列

```python
# CC_AutoAnalyzer.py
from queue import Queue
from PySide6.QtCore import QThread, Signal

class CC_AutoAnalyzer(QThread):
    """自动分析队列，后台处理新照片"""
    
    analysis_complete = Signal(int, dict)  # photo_id, results
    analysis_failed = Signal(int, str)     # photo_id, error
    queue_progress = Signal(int, int)      # current, total
    
    def __init__(self, processor: CC_SkinProcessor, db: CC_Database):
        super().__init__()
        self.processor = processor
        self.db = db
        self.queue = Queue()
        self.running = True
        
    def add_photo(self, photo_path: Path, album_id: int):
        """添加照片到分析队列"""
        self.queue.put((photo_path, album_id))
    
    def run(self):
        """后台处理队列中的照片"""
        while self.running:
            try:
                photo_path, album_id = self.queue.get(timeout=1)
                
                # 添加到数据库
                photo_id = self.db.add_photo(photo_path)
                self.db.add_photo_to_album(photo_id, album_id)
                
                # 检查是否已分析过
                existing = self.db.get_analysis(photo_id)
                if existing and existing.get('face_detected'):
                    continue
                
                # 分析照片
                try:
                    image_rgb = self.processor._load_image(photo_path)
                    point_cloud, mask = self.processor.process_image(image_rgb, return_mask=True)
                    
                    if len(point_cloud) > 0:
                        # 计算统计数据（与 CC_Main.py 中的逻辑相同）
                        results = self._calculate_statistics(point_cloud, mask)
                        self.db.save_analysis(photo_id, results)
                        self.analysis_complete.emit(photo_id, results)
                    else:
                        self.analysis_failed.emit(photo_id, "No face detected")
                        
                except Exception as e:
                    self.analysis_failed.emit(photo_id, str(e))
                    
            except Empty:
                continue
    
    def _calculate_statistics(self, point_cloud, mask):
        """计算统计数据（从 CC_Main.py 复用逻辑）"""
        # ... 与现有的统计计算逻辑相同
        pass
```

#### 4. 修改 CC_Main.py

**A. 添加 "Add Folder Album" 功能**

```python
class CC_MainWindow(QMainWindow):
    def __init__(self):
        # ...existing code...
        
        # 新增：文件夹监控器和自动分析器
        self.folder_watchers = {}  # album_id -> CC_FolderWatcher
        self.auto_analyzer = CC_AutoAnalyzer(self.processor, self.db)
        self.auto_analyzer.start()
        
    def _create_menu(self):
        # ...existing code...
        
        # 添加 "Add Folder Album" 菜单项
        add_folder_album_action = QAction("📁 Add Folder Album...", self)
        add_folder_album_action.triggered.connect(self._add_folder_album)
        file_menu.addAction(add_folder_album_action)
    
    def _add_folder_album(self):
        """创建一个监控文件夹的 Album"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Monitor")
        if not folder:
            return
        
        folder_path = Path(folder)
        album_name = folder_path.name
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "Create Folder Album",
            f"Create album '{album_name}' and monitor folder:\n{folder_path}\n\n"
            f"This will:\n"
            f"• Scan all photos in the folder and subfolders\n"
            f"• Automatically analyze all photos\n"
            f"• Watch for new photos and analyze them automatically\n\n"
            f"Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 创建 Album（保存 folder_path）
        album_id = self.db.create_album(album_name, f"Auto-monitored: {folder_path}")
        self.db.conn.execute(
            "UPDATE albums SET folder_path = ?, auto_scan = 1 WHERE id = ?",
            (str(folder_path), album_id)
        )
        self.db.conn.commit()
        
        # 开始监控和分析
        self._start_folder_monitoring(album_id, folder_path)
        
        # 刷新 UI
        self._load_albums()
    
    def _start_folder_monitoring(self, album_id: int, folder_path: Path):
        """开始监控文件夹"""
        # 创建监控器
        watcher = CC_FolderWatcher(folder_path, self.db)
        watcher.new_photos_found.connect(
            lambda paths: self._on_new_photos(album_id, paths)
        )
        watcher.photos_removed.connect(self._on_photos_removed)
        
        # 初始扫描
        all_photos = watcher.initial_scan()
        QMessageBox.information(
            self,
            "Initial Scan",
            f"Found {len(all_photos)} photos.\n\nStarting automatic analysis..."
        )
        
        # 添加到自动分析队列
        for photo in all_photos:
            self.auto_analyzer.add_photo(photo, album_id)
        
        # 启动文件系统监控
        watcher.start_watching()
        self.folder_watchers[album_id] = watcher
    
    def _on_new_photos(self, album_id: int, paths: List[Path]):
        """处理新发现的照片"""
        for path in paths:
            self.auto_analyzer.add_photo(path, album_id)
        
        # 刷新 UI
        if self.current_album_id == album_id:
            self._load_album_photos(album_id)
    
    def _on_photos_removed(self, paths: List[Path]):
        """处理被删除的照片"""
        # 从数据库中标记为已删除（或直接删除记录）
        for path in paths:
            # 实现删除逻辑
            pass
```

**B. 修改照片选择逻辑（自动显示分析结果）**

```python
class CC_MainWindow(QMainWindow):
    def _select_photo(self, photo_path: Path):
        """选择照片并自动显示分析结果"""
        self.current_photo = photo_path
        self.current_photo_label.setText(f"Selected:\n{str(photo_path)}")
        
        # 从数据库加载分析结果
        photo_id = self.db.add_photo(photo_path)
        analysis = self.db.get_analysis(photo_id)
        
        if analysis and analysis.get('face_detected'):
            # 自动显示分析结果（无需点击 Analyze）
            self._display_analysis_results(analysis)
            
            # 如果需要 3D 可视化，加载 point_cloud
            if analysis.get('point_cloud_data'):
                point_cloud_bytes = analysis['point_cloud_data']
                self.point_cloud = pickle.loads(point_cloud_bytes)
                self.visualize_btn.setEnabled(True)
        else:
            # 尚未分析，显示提示
            self.results_text.setText("⏳ Analysis pending...")
            self.stats_text.setText("Waiting for analysis...")
            self.analyze_btn.setEnabled(True)
    
    def _display_analysis_results(self, analysis: dict):
        """显示分析结果（包括三个柱状图）"""
        # 提取数据
        num_points = analysis.get('num_points', 0)
        mask_coverage = analysis.get('mask_coverage', 0)
        h_mean = analysis.get('hue_mean', 0)
        s_mean = analysis.get('saturation_mean', 0)
        l_mean = analysis.get('lightness_mean', 0)
        
        # 显示基本信息
        self.results_text.setText(
            f"✓ Face detected! (from database)\n"
            f"{num_points:,} points\n"
            f"Coverage: {mask_coverage * 100:.1f}%"
        )
        
        # 显示统计信息（包括三个柱状图的 ASCII 版本）
        self.stats_text.setText(self._format_statistics_text(analysis))
        
        # TODO: 在未来版本中，可以添加图形化的柱状图显示
        # 可以使用 matplotlib 或 pyqtgraph 在 Analysis 面板中嵌入图表
```

#### 5. UI 改进（可选）

**A. 文件夹 Album 的视觉区分**

在 Album 树形列表中，为文件夹 Album 添加特殊图标：

```python
def _load_albums(self):
    # ...existing code...
    
    for album in albums:
        item = QTreeWidgetItem([f"📁 {album['name']}" if album.get('folder_path') else f"📷 {album['name']}"])
        # ...
```

**B. 实时分析进度显示**

```python
class CC_MainWindow(QMainWindow):
    def __init__(self):
        # ...existing code...
        
        # 连接自动分析信号
        self.auto_analyzer.queue_progress.connect(self._update_analysis_progress)
        self.auto_analyzer.analysis_complete.connect(self._on_auto_analysis_complete)
    
    def _update_analysis_progress(self, current: int, total: int):
        """更新分析进度（状态栏）"""
        self.statusBar().showMessage(f"Auto-analyzing: {current}/{total} photos...")
    
    def _on_auto_analysis_complete(self, photo_id: int, results: dict):
        """单个照片分析完成"""
        # 如果当前正在查看这张照片，刷新显示
        if self.current_photo:
            current_photo_id = self.db.add_photo(self.current_photo)
            if current_photo_id == photo_id:
                self._display_analysis_results(results)
```

### 方案 B：独立的 Folder 管理（备选）

如果不想修改 Album 系统，可以创建一个独立的 "Folders" 功能：

```
Folders (根节点)
├── C:\Users\...\Lightroom_Exports
│   ├── Portrait_Session_1
│   ├── Portrait_Session_2
│   └── ...
└── D:\Photos\Studio

Albums (根节点)
├── Best Portraits 2024
├── Client Work
└── ...
```

**优势：** 概念分离，Folders 用于自动监控，Albums 用于手动整理  
**劣势：** UI 更复杂，需要更多开发工作

---

## 🎨 用户体验设计

### 工作流程 1：从 Lightroom 导出并分析

**目标：** 无缝对接 Lightroom Classic 的迭代调整流程

**步骤：**

1. **初始设置（仅一次）**
   ```
   ChromaCloud → File → Add Folder Album
   → 选择 Lightroom 的导出目录（如 C:\LR_Exports\Skin_Tests）
   → 确认创建
   ```

2. **Lightroom 中调整照片**
   ```
   Lightroom Classic:
   - 调整 HSL/Luminance/Orange: +15
   - Export → 导出到 C:\LR_Exports\Skin_Tests\test_001.jpg
   ```

3. **ChromaCloud 自动响应**
   ```
   ChromaCloud:
   - 🔍 自动检测到新文件 test_001.jpg
   - ⚙️ 后台自动分析肤色
   - 💾 分析结果保存到数据库
   - ✅ 状态栏显示 "Analysis complete: test_001.jpg"
   ```

4. **查看分析结果**
   ```
   ChromaCloud:
   - 左侧照片列表：看到 test_001.jpg（可能有 ✓ 标记表示已分析）
   - 点击照片
   - 右侧 Analysis 面板：
     ✓ Face detected!
     12,345 points
     Coverage: 45.2%
     
     📊 Lightness Distribution:
       Low: 15.3%
       Mid: 62.1%
       High: 22.6%
     
     🎨 Hue Distribution:
       Red-Orange: 42.3%
       Normal: 48.5%
       Yellow: 9.2%
     
     💧 Saturation Distribution:
       Low: 18.2%
       Normal: 58.3%
       High: 23.5%
   ```

5. **迭代调整**
   ```
   Lightroom Classic:
   - 观察 ChromaCloud 的数据
   - 发现 Lightness High 只有 22.6%，还不够亮
   - 继续调整 Orange Luminance: +20
   - Export → 覆盖 test_001.jpg
   
   ChromaCloud:
   - 🔍 自动检测到文件更新
   - ⚙️ 重新分析
   - ✅ 更新分析结果
   - 点击照片 → 看到新的数据（Lightness High 提升到 28.3%）
   ```

6. **对比多个版本**
   ```
   Lightroom Classic:
   - Export 多个版本：test_001_v1.jpg, test_001_v2.jpg, test_001_v3.jpg
   
   ChromaCloud:
   - 点击 "Statistics" 按钮
   - 查看三个版本的对比图表
   - 决定哪个版本最好
   ```

### 工作流程 2：批量管理照片集

**场景：** 拍摄了一组人像，想批量分析肤色分布

**步骤：**

1. **添加文件夹**
   ```
   ChromaCloud → Add Folder Album
   → 选择 D:\Photos\Session_2024_01\
   ```

2. **自动处理**
   ```
   ChromaCloud:
   - 扫描发现 45 张照片
   - 后台自动分析全部照片（可能需要几分钟）
   - 进度显示在状态栏
   ```

3. **浏览和筛选**
   ```
   - 左侧：45 张照片的缩略图
   - 点击任意一张 → 右侧立即显示分析结果
   - 无需等待，无需手动点击 Analyze
   ```

4. **统计分析**
   ```
   - 点击 "Statistics" 按钮
   - 查看整个 Session 的肤色分布
   - 发现整体偏暗，可以去 Lightroom 批量调整
   ```

---

## 🔧 技术细节

### 依赖库

需要添加 `watchdog` 用于文件系统监控：

```python
# requirements_cc.txt
watchdog>=3.0.0
```

### 数据库迁移

```sql
-- migration_001_folder_support.sql

-- 添加文件夹监控字段
ALTER TABLE albums ADD COLUMN folder_path TEXT;
ALTER TABLE albums ADD COLUMN auto_scan INTEGER DEFAULT 0;
ALTER TABLE albums ADD COLUMN last_scan_time TIMESTAMP;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_albums_folder ON albums(folder_path);
CREATE INDEX IF NOT EXISTS idx_photos_path ON photos(file_path);

-- 记录迁移
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version) VALUES (1);
```

### 性能优化

1. **批量插入优化**
   ```python
   # 一次性插入多张照片，减少数据库操作
   def add_photos_batch(self, photo_paths: List[Path], album_id: int):
       cursor = self.conn.cursor()
       cursor.executemany("""
           INSERT OR IGNORE INTO photos (file_path, file_name, file_size)
           VALUES (?, ?, ?)
       """, [(str(p), p.name, p.stat().st_size) for p in photo_paths])
       self.conn.commit()
   ```

2. **缓存机制**
   ```python
   # 缓存已分析的照片 ID，避免重复查询
   self.analyzed_cache: Set[int] = set()
   ```

3. **多线程分析**
   ```python
   # 使用线程池并行分析多张照片
   from concurrent.futures import ThreadPoolExecutor
   
   self.executor = ThreadPoolExecutor(max_workers=4)
   ```

### 错误处理

```python
class CC_FolderWatcher(QThread):
    def initial_scan(self):
        try:
            # ...scanning logic...
        except PermissionError:
            self.error.emit(f"Permission denied: {self.folder_path}")
        except Exception as e:
            self.error.emit(f"Scan error: {e}")
```

### 日志记录

```python
logger.info(f"[FolderWatcher] Found {len(all_photos)} photos in {folder_path}")
logger.info(f"[AutoAnalyzer] Analyzing photo: {photo_path.name}")
logger.info(f"[AutoAnalyzer] Analysis complete: {photo_id}")
```

---

## 📝 实现优先级

### Phase 1: 基础功能（必须）

✅ **已具备：**
- Album 管理
- 照片管理
- 批量分析
- 数据库存储
- 分析结果显示

🚧 **需要添加：**
1. 数据库 Schema 扩展（folder_path 字段）
2. CC_FolderWatcher 类（文件夹扫描）
3. CC_AutoAnalyzer 类（自动分析队列）
4. UI: "Add Folder Album" 菜单项
5. UI: 照片选择时自动显示分析结果

**预计工作量：** 2-3 天

### Phase 2: 文件系统监控（推荐）

🔄 **实时监控：**
1. 集成 watchdog 库
2. 实现 FileSystemEventHandler
3. 新文件自动触发分析
4. UI 实时更新

**预计工作量：** 1-2 天

### Phase 3: UI 增强（可选）

🎨 **用户体验优化：**
1. 分析进度实时显示（状态栏或专用进度条）
2. 文件夹 Album 的视觉区分（特殊图标）
3. 照片缩略图显示分析状态（✓ 标记）
4. 在 Analysis 面板嵌入图形化柱状图（matplotlib）

**预计工作量：** 2-3 天

### Phase 4: 高级功能（未来）

💡 **增强特性：**
1. 多文件夹监控（同时监控多个目录）
2. 智能增量分析（只分析变化的照片）
3. 分析历史记录（保存每次调整的版本）
4. 自动备份和恢复
5. 云同步（可选）

**预计工作量：** 每个功能 1-3 天

---

## 🎯 总结与建议

### ✅ 完全可行！

这个功能**完全可以**加到现有的 ChromaCloud 中，而且与现有架构**高度兼容**。

### 推荐实现方案

**方案 A（文件夹作为 Album）** 是最佳选择，因为：

1. **架构兼容性高** - 复用现有的 Album 系统
2. **代码改动少** - 主要是添加新功能，而非重构
3. **用户体验好** - 概念简单，易于理解
4. **实现快速** - 2-3 天即可完成基础功能

### 核心优势

完成后，你的工作流将变成：

```
Lightroom 调整 → 导出 → ChromaCloud 自动分析 → 查看结果 → 再次调整
```

**无需：**
- ❌ 手动添加照片
- ❌ 手动批量分析
- ❌ 反复导入导出

**实现：**
- ✅ 自动发现新照片
- ✅ 自动后台分析
- ✅ 点击即看结果
- ✅ 完美迭代工作流

### 下一步行动

如果你想实现这个功能，我建议：

1. **Phase 1 先行** - 实现基础的文件夹扫描和自动分析
2. **快速验证** - 用你的 Lightroom 导出目录测试工作流
3. **迭代改进** - 根据实际使用体验，再添加 Phase 2 和 Phase 3 的功能

这将极大提升你在 Lightroom 和 ChromaCloud 之间的工作效率！🚀

---

*文档创建日期：2026-02-01*  
*基于 ChromaCloud v1.2 架构*  
*预计实现时间：5-7 天（完整功能）*
