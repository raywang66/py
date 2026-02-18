# ChromaCloud - 子目录统计功能修复 
**日期**: 2026年2月17日

## 🐛 Bug修复

### 问题
```
sqlite3.OperationalError: no such column: p.folder_path
```

### 原因
- `photos` 表中没有 `folder_path` 列
- 尝试查询不存在的列导致SQL错误

### 解决方案
✅ 使用 `p.file_path LIKE '/path/to/folder/%'` 替代
✅ 添加路径规范化处理（`os.path.abspath` + `os.sep`）
✅ 简化查询逻辑

---

## ✨ 功能增强

### 1️⃣ 关于数据库存储

**问题**: Add Folder时，每个子目录的path要存在database里吗？

**答案**: **不需要！**

现在的设计：
- 只存储照片的完整路径 (`file_path`)
- 子目录信息动态扫描，不写数据库
- 使用SQL LIKE模式匹配查询子目录照片

优势：
- 节省存储空间
- 自动适应文件夹结构变化
- 不需要维护额外的文件夹表

### 2️⃣ 智能菜单启用/禁用

**问题**: 从容错角度，如果不满足条件，Disable "View Statistics" menu会更合理吗？

**答案**: **是的，已实现！**

新功能：
```python
# 右键菜单前检查是否有分析数据
has_analyzed_photos = self._check_has_analyzed_photos(data)
stats_action.setEnabled(has_analyzed_photos)

# 无数据时显示提示
if not has_analyzed_photos:
    stats_action.setToolTip("No analyzed photos available")
```

用户体验：
- ✅ 有分析数据 → 菜单可点击
- ⚫ 无分析数据 → 菜单灰色禁用，显示提示
- 🚫 避免点击后才发现"无数据"

### 3️⃣ 增强错误处理

添加了完整的异常处理：
- 输入验证（检查 `album_id` 和 `folder_path`）
- 详细错误日志
- 友好的错误提示对话框

---

## 🔧 修改文件

### CC_Database.py
```python
def get_subfolder_detailed_statistics(album_id, folder_path):
    # 修复：使用 file_path 而非不存在的 folder_path 列
    # 改进：添加路径规范化
    folder_path = os.path.abspath(folder_path) + os.sep
    
    WHERE p.file_path LIKE ?  # 使用 LIKE 匹配
```

### CC_Main.py
```python
# 新增方法
def _check_has_analyzed_photos(data) -> bool:
    """智能检查是否有分析数据"""
    # 快速 COUNT 查询，根据类型使用不同逻辑

# 改进方法
def _show_nav_context_menu(position):
    # 基于数据可用性设置菜单状态
    has_photos = self._check_has_analyzed_photos(data)
    stats_action.setEnabled(has_photos)

def _show_statistics(data):
    # 添加输入验证和异常处理
    try:
        if not album_id or not folder_path:
            QMessageBox.warning(...)
    except Exception as e:
        QMessageBox.critical(...)
```

---

## ✅ 测试验证

- [x] Bug已修复（SQL查询正常）
- [x] 子目录统计正常显示
- [x] 菜单智能启用/禁用
- [x] 错误处理优雅
- [x] macOS路径处理正确

---

## 📝 使用说明

1. **右键子目录查看统计**
   - 找到任何子目录（📁 图标）
   - 右键点击
   - 如果有分析数据，"View Statistics" 可点击
   - 如果无分析数据，菜单灰色显示

2. **数据存储说明**
   - 不需要手动维护子目录列表
   - 系统自动从照片路径推断子目录
   - 文件夹结构变化自动适应

3. **性能优化**
   - 菜单显示前快速检查（COUNT + LIMIT 1）
   - 只在需要时加载完整统计数据
   - 使用数据库索引加速查询

---

**问题已完全解决！** 🎉

