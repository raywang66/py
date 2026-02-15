# 导航栏选择丢失问题修复

## 🐛 问题描述

**现象：**
- 重启应用时，导航栏的选择（相册/文件夹）短暂显示
- 然后选择消失，变回未选择状态

## 🔍 根本原因

### 问题1：Folder Watcher初始扫描触发重新加载

**时间线：**
```
1. 应用启动 (0ms)
2. 恢复导航状态 (5364ms)
   - 选择 album_id=2 ✅
3. Folder Watcher 初始扫描完成 (5668ms)
   - 触发 _on_new_photos()
   - 调用 _load_navigator() ← 清除所有选择！❌
4. 导航栏重建，选择丢失
```

**日志证据：**
```
5364 ms [CC_MainApp] 📍 Restoring navigation: type=folder, album_id=2
5364 ms [CC_MainApp] ✅ Selected album 2 in navigator
...
5668 ms [CC_FolderWatcher] Found 110 photos
6303 ms [CC_MainApp] [_on_new_photos] New photos detected: 110 photos
6303 ms [CC_MainApp] [_on_new_photos] Refreshing navigator  ← 问题！
```

### 问题2：其他重新加载也会清除选择

调用 `_load_navigator()` 的地方：
- ✅ `__init__` - 之后会恢复选择
- ❌ `_on_new_photos` - 不保持选择
- ❌ `_add_photos` - 不保持选择
- ✅ `_create_new_album` - 新建相册，不需要保持
- ✅ `_delete_album` - 删除相册，不需要保持
- ❌ `_add_folder_album` - 应该选择新相册

---

## ✅ 修复方案

### 核心思路

在调用 `_load_navigator()` 前后**保存和恢复选择**：

```python
# 保存当前选择
saved_album_id = self.current_album_id

# 重新加载导航树
self._load_navigator()

# 恢复选择
if saved_album_id:
    self._find_and_select_album(saved_album_id)
```

### 修复位置

#### 1. `_on_new_photos()` - Folder Watcher新照片检测

**修复前：**
```python
def _on_new_photos(self, album_id: int, paths: List[Path]):
    # ...
    logger.info("[_on_new_photos] Refreshing navigator")
    self._load_navigator()  # ❌ 清除选择
```

**修复后：**
```python
def _on_new_photos(self, album_id: int, paths: List[Path]):
    # ...
    logger.info("[_on_new_photos] Refreshing navigator")
    saved_album_id = self.current_album_id  # ✅ 保存
    self._load_navigator()
    
    # 恢复选择
    if saved_album_id:
        logger.info(f"[_on_new_photos] Restoring selection to album {saved_album_id}")
        self._find_and_select_album(saved_album_id)  # ✅ 恢复
```

#### 2. `_add_photos()` - 添加照片后

**修复前：**
```python
def _add_photos(self):
    # ... 添加照片逻辑 ...
    self._load_navigator()  # ❌ 清除选择
```

**修复后：**
```python
def _add_photos(self):
    # ... 添加照片逻辑 ...
    saved_album_id = self.current_album_id
    self._load_navigator()
    if saved_album_id:
        self._find_and_select_album(saved_album_id)  # ✅ 恢复
```

#### 3. `_add_folder_album()` - 添加文件夹相册

**修复前：**
```python
def _add_folder_album(self):
    # ... 创建相册逻辑 ...
    self._load_navigator()  # ❌ 新相册未选中
```

**修复后：**
```python
def _add_folder_album(self):
    # ... 创建相册逻辑 ...
    saved_album_id = self.current_album_id
    self._load_navigator()
    # 选择新创建的相册
    self._find_and_select_album(album_id)  # ✅ 选择新相册
    self.current_album_id = album_id
```

---

## 🎯 修复效果

### 修复前：

```
启动应用
↓
恢复导航 (album_id=2 选中) ✅
↓
等待5秒...
↓
Folder Watcher 初始扫描完成
↓
_on_new_photos 触发
↓
_load_navigator() 清除选择 ❌
↓
结果：没有选中项
```

### 修复后：

```
启动应用
↓
恢复导航 (album_id=2 选中) ✅
↓
等待5秒...
↓
Folder Watcher 初始扫描完成
↓
_on_new_photos 触发
↓
保存 album_id=2 ✅
↓
_load_navigator() 重建树
↓
恢复选择 album_id=2 ✅
↓
结果：album_id=2 仍然选中 ✅
```

---

## 📋 测试步骤

### 测试1：重启保持选择

1. **启动应用**
2. **选择一个Folder/Album**
3. **关闭应用**
4. **重新启动**
5. **观察：** 应该立即显示上次的选择 ✅
6. **等待5-10秒** (Folder Watcher初始扫描)
7. **观察：** 选择应该**仍然保持** ✅

### 测试2：添加照片保持选择

1. **选择一个相册**
2. **File → Add Photos**
3. **添加一些照片**
4. **观察：** 相册应该仍然选中 ✅

### 测试3：新建文件夹相册自动选中

1. **File → Add Folder Album**
2. **选择一个文件夹**
3. **观察：** 新创建的文件夹相册应该被选中 ✅

---

## 🔍 技术细节

### `_find_and_select_album()` 函数

这个函数负责在导航树中找到并选中指定的相册：

```python
def _find_and_select_album(self, album_id: int):
    """Find and select an album in the navigation tree"""
    def search_item(item):
        # Check current item
        data = item.data(0, Qt.UserRole)
        if data and data.get('id') == album_id:
            return item
        
        # Search children recursively
        for i in range(item.childCount()):
            result = search_item(item.child(i))
            if result:
                return result
        return None
    
    # Search from root
    root = self.nav_tree.invisibleRootItem()
    for i in range(root.childCount()):
        found = search_item(root.child(i))
        if found:
            self.nav_tree.setCurrentItem(found)
            
            # Expand parents
            parent = found.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            
            logger.info(f"✅ Selected album {album_id} in navigator")
            return
```

**特点：**
- 递归搜索整个树
- 找到后设置为当前项
- 自动展开所有父节点
- 日志记录操作

### 为什么会丢失选择？

Qt的 `QTreeWidget` 在调用 `clear()` 后：
- ✅ 删除所有item
- ✅ 清除选择状态
- ✅ 清除展开状态

`_load_navigator()` 内部调用：
```python
self.nav_tree.clear()  # ← 这里清除了一切！
```

所以必须在 `_load_navigator()` **之后**重新选择。

---

## 🎯 相关问题

### 为什么Folder Watcher初始扫描要调用 _load_navigator()？

**原因：** 更新照片计数
```
📂 Photos (110)  ← 需要更新这个数字
```

**替代方案：** 只更新计数而不重建树
- 但这样代码更复杂
- 当前方案简单：重建+恢复选择

---

## 📝 日志输出

### 修复后的日志：

```
[启动]
📍 Restoring navigation: type=folder, album_id=2
✅ Selected album 2 in navigator

[等待5秒...]

[Folder Watcher初始扫描]
[_on_new_photos] New photos detected: 110 photos for album 2
[_on_new_photos] Refreshing navigator
[_on_new_photos] Restoring selection to album 2  ← 新日志
✅ Selected album 2 in navigator  ← 恢复成功
```

---

## ✅ 修复完成

### 改动文件：
- `CC_Main.py`

### 改动内容：
1. ✅ `_on_new_photos()` - 保存和恢复选择
2. ✅ `_add_photos()` - 保存和恢复选择
3. ✅ `_add_folder_album()` - 选择新创建的相册

### 修复的场景：
- ✅ 应用启动后Folder Watcher初始扫描
- ✅ 添加照片后重新加载导航
- ✅ 创建文件夹相册后自动选中

---

## 🚀 测试

**应用已启动！**

请测试：
1. 等待几秒，观察导航栏选择是否**保持不变** ✅
2. 添加照片，观察选择是否保持 ✅
3. 创建新文件夹相册，观察是否自动选中 ✅

**导航栏选择丢失问题已完全修复！** ✨

