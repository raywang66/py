# ChromaCloud - Subfolder Statistics Feature (Updated)
**Date**: February 17, 2026  
**Status**: ✅ Fixed and Enhanced

## Bug Fix Summary

### 🐛 Issue Found
```
sqlite3.OperationalError: no such column: p.folder_path
```

**Root Cause**: 
- `photos` 表中没有 `folder_path` 列
- 查询错误地尝试使用不存在的列

**Fix Applied**:
- 改为使用 `file_path` 列（完整文件路径）
- 使用 `LIKE` 模式匹配来查找子目录中的文件
- 路径规范化以确保正确匹配

---

## New Feature: View Statistics for Subfolders ✅

### 功能描述
现在可以在任何子目录上右键点击，选择 "View Statistics" 来查看该子目录（包括其所有子子目录）的照片统计数据。

### 关键问题回答

#### 1️⃣ **Add Folder时，每个子目录的path要存在database里吗？**

**答案：不需要！**

当前设计方案：
- ✅ 只存储照片的完整路径 (`file_path`)
- ✅ 子目录结构**动态扫描**，不写入数据库
- ✅ 使用 SQL LIKE 模式匹配来查询子目录的照片

**优势**:
```
📁 存储模式：
   photos表:
   - /path/to/folder/subfolder/photo1.jpg  ← 只存这个
   - /path/to/folder/subfolder/photo2.jpg
   - /path/to/folder/another/photo3.jpg
   
📊 查询子目录统计：
   WHERE file_path LIKE '/path/to/folder/subfolder/%'
   ✓ 自动匹配所有子子目录
   ✓ 无需维护文件夹表
   ✓ 节省存储空间
```

#### 2️⃣ **从容错的角度，如果不满足条件，Disable "View Statistics" menu会更合理吗？**

**答案：是的，已实现！**

**新增智能菜单启用/禁用**:
```python
def _check_has_analyzed_photos(data) -> bool:
    """检查是否有已分析的照片"""
    # 快速 COUNT 查询
    # 如果没有分析数据 → 菜单项禁用
    # 如果有分析数据 → 菜单项启用
```

**用户体验**:
- ✅ 有分析数据 → "View Statistics" 可点击
- ⚫ 无分析数据 → "View Statistics" 灰色显示，鼠标悬停显示提示
- 🚫 避免点击后才显示"无数据"的尴尬

---

### 实现细节

#### 1. 数据库方法（已修复）
`get_subfolder_detailed_statistics()` in `CC_Database.py`:

```python
def get_subfolder_detailed_statistics(self, album_id: int, folder_path: str):
    """Get statistics for photos in subfolder and its subdirectories"""
    import os
    
    # Normalize path with trailing separator
    folder_path = os.path.abspath(folder_path)
    if not folder_path.endswith(os.sep):
        folder_path += os.sep
    
    # Use LIKE to match all files in folder and subdirectories
    cursor.execute("""
        SELECT ... FROM photos p
        WHERE p.file_path LIKE ?
    """, (folder_path + '%',))
```

**修复内容**:
- ❌ 删除：`p.folder_path` （列不存在）
- ✅ 改用：`p.file_path LIKE '/path/%'`
- ✅ 添加：路径规范化处理

#### 2. 智能菜单启用（新增）
`_check_has_analyzed_photos()` in `CC_Main.py`:

```python
# 在显示菜单前检查
has_analyzed_photos = self._check_has_analyzed_photos(data)
stats_action.setEnabled(has_analyzed_photos)

if not has_analyzed_photos:
    stats_action.setToolTip("No analyzed photos available")
```

**特点**:
- ⚡ 快速查询（使用 COUNT + LIMIT 1）
- 🎯 针对不同类型（album/folder/subfolder）使用不同查询
- 🛡️ 异常安全（出错时默认禁用）

#### 3. 增强错误处理（新增）
`_show_statistics()` 改进:

```python
try:
    # Validate inputs
    if not album_id or not folder_path:
        QMessageBox.warning(...)
        return
    
    # Get statistics...
    
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    QMessageBox.critical(...)
```

**改进**:
- ✅ 输入验证
- ✅ 详细错误日志
- ✅ 友好错误提示

---

### 使用方法

1. **在导航树中找到子目录**
   ```
   📂 Folders (1)
     📂 Downloads (189)
       📁 Nano Banana (14)  ← 右键这里
       📁 Skin Tones (2)    ← 或这里
   ```

2. **右键点击子目录**
   - 如果有分析数据 → "View Statistics" **可点击**
   - 如果无分析数据 → "View Statistics" **灰色禁用**

3. **查看统计数据**
   - 窗口标题显示子目录名称
   - 显示该目录及所有子子目录的照片统计
   - 所有图表正常工作

---

### 技术亮点

#### 🎯 SQL路径匹配
```sql
-- 标准化路径（确保以分隔符结尾）
folder_path = '/path/to/folder/'

-- 匹配所有子文件
WHERE p.file_path LIKE '/path/to/folder/%'

-- 匹配结果：
-- ✓ /path/to/folder/photo.jpg
-- ✓ /path/to/folder/sub/photo.jpg  
-- ✓ /path/to/folder/sub/deep/photo.jpg
-- ✗ /path/to/other/photo.jpg
```

#### 🔒 防御性编程
```python
# 1. 路径规范化
folder_path = os.path.abspath(folder_path)
if not folder_path.endswith(os.sep):
    folder_path += os.sep

# 2. 输入验证
if not album_id or not folder_path:
    return False

# 3. 异常处理
try:
    ...
except Exception as e:
    logger.error(...)
    return False  # 安全默认值
```

#### ⚡ 性能优化
```sql
-- 快速检查（不加载数据）
SELECT COUNT(*) ... LIMIT 1

-- vs 完整查询（仅在需要时）
SELECT * FROM ...
```

---

### 兼容性

- ✅ 完全向后兼容
- ✅ 不影响现有相册和文件夹统计
- ✅ 适用于多层嵌套子目录
- ✅ macOS, Windows, Linux 全平台支持
- ✅ 优雅处理错误和边界情况

---

### 文件修改清单

**CC_Database.py**:
- 🐛 修复: `get_subfolder_detailed_statistics()` - 使用 `file_path` 而非 `folder_path`
- ✨ 改进: 添加路径规范化和 `os.sep` 处理

**CC_Main.py**:
- ✨ 新增: `_check_has_analyzed_photos()` - 智能菜单启用/禁用
- 🐛 修复: `_show_nav_context_menu()` - 基于数据可用性设置菜单状态  
- ✨ 改进: `_show_statistics()` - 添加输入验证和错误处理

---

### 测试清单

- [x] 单层子目录统计
- [x] 多层嵌套子目录统计
- [x] 根目录直接照片统计
- [x] 无分析数据时菜单禁用
- [x] 有分析数据时菜单启用
- [x] 离线USB缩略图显示
- [x] 错误情况优雅处理
- [x] macOS路径分隔符正确性
- [x] Windows路径分隔符正确性

---

## 用户反馈

> "FolderWatcher 工作的很好，它对多层的子目录维护的相当好，每个子目录里的照片都显示在括号里，一目了然。子目录里新增的照片也能自动加进来。如果在任何一个子目录上能够右击，并进行'View Statistics'就更好了。"

✅ **已实现并增强！** 
- 任何子目录都可以右键查看统计
- 智能判断是否有数据，自动启用/禁用菜单
- 优雅处理所有错误情况


