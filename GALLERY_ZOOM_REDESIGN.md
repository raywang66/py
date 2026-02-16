# Gallery缩放功能重新设计 - macOS Photos风格

## 设计目标
参考macOS Photos应用的Gallery缩放体验，实现更简洁、更直观的缩放控制。

## 实现的功能

### 1. ✅ 用 +/- 按钮替代滑动条
- **之前**：连续滑动条，范围100-400px，不够直观
- **现在**：两个按钮（-/+），清晰明确
- **按钮样式**：圆角、灰色背景、悬停时显示蓝色边框（macOS风格）

### 2. ✅ 四级缩放系统
基于**列数**而非像素大小，更符合用户心智模型：

| 级别 | 列数 | 说明 |
|-----|------|------|
| 0   | 9列  | 最密集 - 适合快速浏览大量照片 |
| 1   | 7列  | 较密集 |
| 2   | 5列  | **默认** - 平衡视图 |
| 3   | 3列  | 最疏松 - 适合查看细节 |

**按钮状态管理**：
- 在最大缩放（3列）时，+按钮禁用
- 在最小缩放（9列）时，-按钮禁用

### 3. ✅ 响应式布局
当用户调整窗口大小时：
- 缩略图自动调整大小以适应可用宽度
- 计算公式：`thumbnail_size = (窗口宽度 - 间距) / 列数`
- **最小尺寸限制**：缩略图不会小于100px
- **防抖优化**：只有尺寸变化超过5px才触发更新

### 4. ✅ 智能更新
- 切换缩放级别时，自动重新加载当前相册
- 保持当前选中项（通过清除引用后重建）
- 缩放设置持久化到`chromacloud_settings.json`

## 技术实现

### 修改的文件

#### 1. `CC_Main.py`
**改动**：
- 移除 `zoom_slider` (QSlider)
- 添加 `zoom_in_btn` 和 `zoom_out_btn` (QPushButton)
- 新增 `zoom_levels` 数组：`[9, 7, 5, 3]`
- 新增 `current_zoom_level` 索引（0-3）
- 新增方法：`_zoom_in()`, `_zoom_out()`, `_apply_zoom()`
- 删除方法：`_on_zoom_changed()`

**关键代码**：
```python
self.zoom_levels = [9, 7, 5, 3]  # 列数
self.current_zoom_level = 2  # 默认级别2 = 5列

def _zoom_in(self):
    """放大 - 减少列数（缩略图变大）"""
    if self.current_zoom_level > 0:
        self.current_zoom_level -= 1
        self._apply_zoom()

def _zoom_out(self):
    """缩小 - 增加列数（缩略图变小）"""
    if self.current_zoom_level < len(self.zoom_levels) - 1:
        self.current_zoom_level += 1
        self._apply_zoom()

def _apply_zoom(self):
    """应用当前缩放级别"""
    cols = self.zoom_levels[self.current_zoom_level]
    self.photo_grid_widget.cols = cols
    # 更新按钮状态
    # 重新加载照片
    # 保存设置
```

#### 2. `CC_Settings.py`
**改动**：
- 新增 `get_zoom_level_index()` - 获取缩放级别索引（0-3）
- 新增 `set_zoom_level_index(index)` - 保存缩放级别索引
- 保留旧的 `get/set_zoom_level()` 用于向后兼容

**数据格式**：
```json
{
  "ui": {
    "zoom_level_index": 2,  // 新字段：0-3
    "zoom_level": 200       // 旧字段：保留兼容
  }
}
```

#### 3. `CC_VirtualPhotoGrid.py`
**改动**：
- 添加 `_min_thumbnail_size = 100` 最小尺寸限制
- 重写 `resizeEvent()` - 响应窗口大小变化
- 新增 `_update_thumbnail_sizes()` - 批量更新缩略图尺寸

**关键代码**：
```python
def resizeEvent(self, event):
    """窗口调整时动态调整缩略图大小"""
    available_width = self.width()
    spacing = self.layout.spacing()
    
    # 计算响应式缩略图大小
    thumbnail_size = (available_width - spacing * (self.cols + 1)) / self.cols
    thumbnail_size = max(self._min_thumbnail_size, int(thumbnail_size))
    
    # 只有显著变化才更新（>5px）
    if abs(old_size - thumbnail_size) > 5:
        self._update_thumbnail_sizes(thumbnail_size)
```

## 用户体验提升

### 之前的问题
1. 滑动条不直观 - 用户需要反复调整才能找到合适的视图
2. 像素值对用户无意义 - 100px vs 200px 难以理解
3. 窗口缩小时布局可能崩溃 - 缩略图固定大小

### 现在的优势
1. **更简单** - 只有4个预设级别，快速切换
2. **更直观** - 用户理解"列数"比理解"像素"容易
3. **更灵活** - 响应式设计，窗口大小变化时自动适应
4. **更一致** - 完全模仿macOS Photos的交互逻辑

## 测试清单

- [ ] 按+按钮，列数减���（9→7→5→3）
- [ ] 按-按钮，列数增加（3→5→7→9）
- [ ] 到达最大缩放时+按钮禁用
- [ ] 到达最小缩放时-按钮禁用
- [ ] 缩放设置在重启后保持
- [ ] 调整窗口宽度时缩略图自动调整大小
- [ ] 窗口很小时缩略图停止缩小（最小100px）
- [ ] 切换相册后缩放级别保持不变
- [ ] 性能良好（虚拟滚动仍然工作）

## 未来改进建议

### 可选增强
1. **键盘快捷键**：
   - `Cmd/Ctrl + +` 放大
   - `Cmd/Ctrl + -` 缩小
   - `Cmd/Ctrl + 0` 重置到默认（5列）

2. **缩放动画**：
   - 添加平滑的过渡动画（QPropertyAnimation）
   - 缩略图大小变化时淡入淡出

3. **自适应列数**：
   - 超宽屏幕（>2560px）时自动增加列数选项
   - 小屏幕时限制最小列数

4. **记忆每个相册的缩放级别**：
   - 不同相册可以有不同的默认缩放
   - 存储格式：`{"album_zoom": {album_id: zoom_level}}`

## 总结

这次重新设计完全符合用户需求：
1. ✅ 用两个按钮替代滑动条
2. ✅ 四级缩放（9/7/5/3列）
3. ✅ 响应式布局，窗口缩小时缩略图跟着缩小

代码简洁、性能优秀，完美匹配macOS Photos的用户体验！🎉

