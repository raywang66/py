# 数据库逻辑修复总结
Date: 2026-02-02

## 问题描述

你发现了两个严重的逻辑错误：

### ❌ 错误 1: 未经授权扫描文件系统
- **问题**: 当数据库重建后（所有表为空），点击"All Photos"竟然显示157张照片
- **原因**: `_load_all_photos()` 直接扫描 `Photos` 文件夹（文件系统），而不是查询数据库
- **影响**: 绕过了数据库的授权机制，显示未添加到数据库的照片

### ❌ 错误 2: 孤立的缩略图缓存
- **问题**: `thumbnail_cache` 表有79条记录，但 `photos` 表为空
- **原因**: 缓存表没有自动清理机制，导致孤立数据存在
- **影响**: `thumbnail_cache` 应该是被动的，必须外联到 `photos` 表

## 修复方案

### ✅ 修复 1: CC_Database.py - 添加 get_all_photos() 方法

**文件**: `C:\Users\rwang\lc_sln\py\CC_Database.py`
**位置**: 第 387-393 行（在 `get_project_photos()` 之后）

```python
def get_all_photos(self) -> List[Dict]:
    """Get all photos from database - ONLY shows photos that have been explicitly added"""
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT * FROM photos
        ORDER BY added_at DESC
    """)
    return [dict(row) for row in cursor.fetchall()]
```

### ✅ 修复 2: CC_Main.py - 修改 _load_all_photos() 使用数据库

**文件**: `C:\Users\rwang\lc_sln\py\CC_Main.py`
**位置**: 第 1317-1327 行

**修改前**:
```python
def _load_all_photos(self):
    """Load all photos from Photos folder"""
    self.current_album_id = None
    photos_dir = Path(__file__).parent / "Photos"
    if not photos_dir.exists():
        return

    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    if RAWPY_AVAILABLE:
        extensions.extend(['*.arw', '*.nef', '*.cr2', '*.cr3', '*.dng'])

    photos = []
    for ext in extensions:
        photos.extend(photos_dir.glob(ext))  # ❌ 扫描文件系统
    photos.sort()

    self._display_photos(photos)
    self.photo_header.setText(f"📷 All Photos ({len(photos)})")
```

**修改后**:
```python
def _load_all_photos(self):
    """Load all photos from database - NOT from file system!"""
    self.current_album_id = None
    
    # ✅ CORRECT: Load from database, NOT file system
    # Only shows photos that have been explicitly added to the database
    photos = self.db.get_all_photos()
    photo_paths = [Path(p['file_path']) for p in photos]
    
    self._display_photos(photo_paths)
    self.photo_header.setText(f"📷 All Photos ({len(photo_paths)})")
```

### ✅ 修复 3: CC_Database.py - 添加清理孤立缓存的方法

**文件**: `C:\Users\rwang\lc_sln\py\CC_Database.py`
**位置**: 第 652-665 行（在 `cleanup_old_thumbnail_cache()` 之后）

```python
def cleanup_orphaned_thumbnails(self):
    """
    Clean up orphaned thumbnail cache entries that have no corresponding photos record.
    Thumbnail cache is PASSIVE - it must be linked to photos table!
    """
    cursor = self.conn.cursor()
    cursor.execute("""
        DELETE FROM thumbnail_cache 
        WHERE photo_path NOT IN (SELECT file_path FROM photos)
    """)
    deleted = cursor.rowcount
    self.conn.commit()
    logger.info(f"Cleaned up {deleted} orphaned thumbnail cache entries")
    return deleted
```

### ✅ 修复 4: CC_Database.py - 自动清理孤立缓存

**文件**: `C:\Users\rwang\lc_sln\py\CC_Database.py`
**位置**: 第 22-36 行（`__init__` 方法）

**修改前**:
```python
def __init__(self, db_path: Optional[Path] = None):
    """Initialize database connection"""
    if db_path is None:
        db_path = Path(__file__).parent / "chromacloud.db"

    self.db_path = db_path
    self.conn = sqlite3.connect(str(db_path))
    self.conn.row_factory = sqlite3.Row

    self._create_tables()
    logger.info(f"Database initialized: {db_path}")
```

**修改后**:
```python
def __init__(self, db_path: Optional[Path] = None):
    """Initialize database connection"""
    if db_path is None:
        db_path = Path(__file__).parent / "chromacloud.db"

    self.db_path = db_path
    self.conn = sqlite3.connect(str(db_path))
    self.conn.row_factory = sqlite3.Row

    self._create_tables()
    
    # Clean up orphaned thumbnail cache on startup
    # Ensures cache integrity - thumbnails must have corresponding photos!
    self.cleanup_orphaned_thumbnails()
    
    logger.info(f"Database initialized: {db_path}")
```

## 修复效果

### 修复前的行为:
1. 删除 `chromacloud.db`
2. 运行 `CC_Main.py`
3. 点击 "All Photos" → 显示 157 张照片 ❌（从文件系统扫描）
4. `thumbnail_cache` 有 79 条孤立记录 ❌

### 修复后的行为:
1. 删除 `chromacloud.db`
2. 运行 `CC_Main.py`
3. 数据库初始化时自动清理孤立缓存 ✅
4. 点击 "All Photos" → 显示 0 张照片 ✅（数据库为空）
5. 创建 Album → 显示 0 张照片 ✅（未添加照片）
6. 添加照片到 Album → 照片出现在 Album 中 ✅
7. 点击 "All Photos" → 显示所有已添加的照片 ✅

## 核心原则

### 1. 数据来源的唯一性
- **所有照片显示必须来自数据库**
- **禁止绕过数据库直接扫描文件系统**
- 用户必须显式添加照片（通过 "+ Add Photos" 按钮）

### 2. 缓存的被动性
- `thumbnail_cache` 是**被动服务**，不能自主存在
- 必须有对应的 `photos` 表记录
- 启动时自动清理孤立记录

### 3. 授权机制
- 只有用户授权添加的照片才能显示
- 数据库是权限控制的唯一入口
- 文件系统仅作为存储，不作为数据源

## 验证步骤

请按以下步骤验证修复:

1. **删除数据库** (如果还没删除):
   ```powershell
   Remove-Item C:\Users\rwang\lc_sln\py\chromacloud.db
   ```

2. **运行 CC_Main.py**:
   ```powershell
   cd C:\Users\rwang\lc_sln\py
   .\start_chromacloud.bat
   ```

3. **验证 "All Photos"**:
   - 点击左侧导航的 "📸 All Photos"
   - **应该显示**: "📷 All Photos (0)"
   - **不应该显示**: 157 张照片

4. **验证 Album**:
   - 右键点击 "Albums" → "New Album"
   - 创建一个新 Album
   - 点击这个 Album
   - **应该显示**: "(0 photos)"

5. **添加照片**:
   - 在 Album 视图中点击 "+ Add Photos"
   - 选择要添加的照片
   - 照片应该出现在 Album 中
   - 再点击 "All Photos"，应该能看到刚添加的照片

## 文件清单

修改的文件:
- ✅ `CC_Database.py` - 3处修改
  - 添加 `get_all_photos()` 方法
  - 添加 `cleanup_orphaned_thumbnails()` 方法
  - 在 `__init__` 中调用清理

- ✅ `CC_Main.py` - 1处修改
  - 修改 `_load_all_photos()` 使用数据库而非文件系统

## 总结

这两个修复确保了 ChromaCloud 的数据完整性和授权机制:

1. **数据库是唯一的数据源** - 所有显示必须来自数据库
2. **缓存必须与数据关联** - 防止孤立数据污染数据库
3. **用户控制数据可见性** - 只显示用户明确添加的照片

修复后，系统行为符合预期：空数据库 = 0 张照片显示。
