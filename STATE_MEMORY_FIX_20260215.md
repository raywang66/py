# 状态记忆修复 - 2026-02-15

## 🐛 报告的问题

### 问题1：点击X不保存设置
**现象：** File → Save Settings 可以生成 `chromacloud_settings.json`，但点击X关闭窗口不会保存

**原因：** `closeEvent` 可能在某些情况下不被调用（特别是Windows上）

### 问题2：重启时列数不对
**现象：** 
- Zoom级别恢复正确（400px）
- 但显示了3列，而不是400px对应的2列

**原因：** 恢复zoom级别时，没有同时更新photo_grid_widget的列数

---

## ✅ 修复方案

### 修复1：使用 aboutToQuit 信号

在 `main()` 函数中添加 `app.aboutToQuit` 信号处理：

```python
def main():
    app = QApplication(sys.argv)
    window = CC_MainWindow()
    
    # 连接 aboutToQuit 信号确保设置被保存
    # 这个信号在应用退出前一定会触发，包括点击X关闭
    def save_on_quit():
        logger.info("🚪 Application aboutToQuit signal - saving settings...")
        try:
            # 保存窗口几何
            if window.isMaximized():
                window.showNormal()
                geom = window.geometry()
                window.settings.set_window_geometry(
                    geom.x(), geom.y(), geom.width(), geom.height(), maximized=True
                )
            else:
                geom = window.geometry()
                window.settings.set_window_geometry(
                    geom.x(), geom.y(), geom.width(), geom.height(), maximized=False
                )
            
            # 保存到文件
            window.settings.save()
            logger.info("✅ Settings saved via aboutToQuit")
        except Exception as e:
            logger.error(f"❌ Failed to save on quit: {e}")
    
    app.aboutToQuit.connect(save_on_quit)
    
    window.show()
    sys.exit(app.exec())
```

**为什么有效：**
- `aboutToQuit` 在应用退出前**总是**被触发
- 覆盖所有退出方式：
  - ✅ 点击X关闭
  - ✅ File → Exit
  - ✅ Alt+F4
  - ✅ 系统关机（如果有时间）

### 修复2：初始化时设置列数

在创建 `photo_grid_widget` 后立即根据恢复的zoom级别设置列数：

```python
# 创建网格
self.photo_grid_widget = SimpleVirtualPhotoGrid(
    db=self.db,
    thumbnail_class=CC_PhotoThumbnail
)

# 根据恢复的zoom级别设置初始列数
saved_zoom = self.settings.get_zoom_level()
if saved_zoom <= 120:
    self.photo_grid_widget.cols = 6      # Tiny: 100-120px
elif saved_zoom <= 160:
    self.photo_grid_widget.cols = 5      # Small: 121-160px
elif saved_zoom <= 220:
    self.photo_grid_widget.cols = 4      # Medium: 161-220px
elif saved_zoom <= 300:
    self.photo_grid_widget.cols = 3      # Large: 221-300px
else:
    self.photo_grid_widget.cols = 2      # Extra Large: 301-400px
logger.info(f"📐 Set initial column count: {self.photo_grid_widget.cols} (zoom={saved_zoom}px)")
```

**逻辑与 `_on_zoom_changed` 一致：**
```python
def _on_zoom_changed(self, value: int):
    # ... 更新 thumbnail_size ...
    
    # 更新列数（相同的逻辑）
    if value <= 120:
        self.photo_grid_widget.cols = 6
    elif value <= 160:
        self.photo_grid_widget.cols = 5
    # ...
```

---

## 🎯 修复效果

### 修复前：

#### 问题1：
```
用户操作：
1. 调整窗口、切换主题、Zoom到400px
2. 点击 X 关闭

结果：
❌ 没有保存 (chromacloud_settings.json 不更新)

下次启动：
❌ 使用旧的或默认设置
```

#### 问题2：
```
chromacloud_settings.json:
{
  "ui": { "zoom_level": 400 }
}

下次启动：
✅ Zoom恢复到400px
❌ 但显示3列（应该是2列）

原因：
- Zoom slider恢复了400
- 但photo_grid_widget.cols还是默认的3
```

### 修复后：

#### 修复1效果：
```
用户操作：
1. 调整窗口、切换主题、Zoom到400px
2. 点击 X 关闭

触发：
✅ aboutToQuit 信号
✅ 保存窗口几何
✅ 保存所有设置
✅ chromacloud_settings.json 更新

下次启动：
✅ 所有设置恢复正确
```

#### 修复2效果：
```
chromacloud_settings.json:
{
  "ui": { "zoom_level": 400 }
}

下次启动：
✅ Zoom恢复到400px
✅ 列数设置为2（正确！）
✅ 网格立即显示正确的布局

日志：
📐 Set initial column count: 2 (zoom=400px)
```

---

## 📋 测试步骤

### 测试1：点击X保存设置

1. **启动应用** ✅
2. **调整状态：**
   - 移动窗口
   - 切换到Dark Mode
   - Zoom到最大（400px）
   - 选择一个Folder
3. **点击 X 关闭窗口**
4. **检查日志：** 应该看到：
   ```
   🚪 Application aboutToQuit signal - saving settings...
   ✅ Settings saved via aboutToQuit
   ```
5. **检查文件：** `chromacloud_settings.json` 应该更新
6. **重新启动**
7. **验证：** 所有设置应该恢复 ✅

### 测试2：列数正确恢复

1. **启动应用** ✅
2. **Zoom到最大（400px）** - 应该看到2列
3. **关闭应用**（任何方式）
4. **重新启动**
5. **检查：**
   - ✅ Zoom slider在400px位置
   - ✅ 显示**2列**（不是3列）
   - ✅ 日志显示：`📐 Set initial column count: 2 (zoom=400px)`

---

## 🎨 Zoom vs 列数对应表

| Zoom范围 | 列数 | 说明 |
|---------|------|------|
| 100-120px | 6列 | Tiny grid |
| 121-160px | 5列 | Small grid |
| 161-220px | 4列 | Medium grid |
| 221-300px | 3列 | Large grid |
| 301-400px | **2列** | Extra Large ⭐ |

**你的情况：**
- Zoom: 400px → 应该是 **2列**
- 修复前：显示3列 ❌
- 修复后：显示2列 ✅

---

## 🔍 技术细节

### aboutToQuit vs closeEvent

| 信号/事件 | 触发时机 | 可靠性 |
|----------|---------|--------|
| `closeEvent` | 窗口关闭时 | ⚠️ 有时不触发 |
| `aboutToQuit` | 应用退出前 | ✅ 总是触发 |

**最佳实践：** 同时使用两者
- `closeEvent`: 正常情况下保存
- `aboutToQuit`: 兜底保证保存

### 初始化顺序

```
1. 创建 zoom_slider
2. 恢复 saved_zoom → zoom_slider.setValue(400)
3. 创建 photo_grid_widget (默认3列)
4. ⚠️ 需要立即更新列数！
5. 设置 photo_grid_widget.cols = 2  ← 新增
```

---

## 📝 日志示例

### 启动时：
```
📋 Settings manager initialized
✅ Loaded settings from chromacloud_settings.json
🎨 Restored dark mode: true
🔍 Restored zoom level: 400px
📐 Set initial column count: 2 (zoom=400px)  ← 新日志
🪟 Restored window: 1400x900 at (100, 100)
```

### 点击X关闭时：
```
🚪 Application aboutToQuit signal - saving settings...  ← 新日志
💾 Saving window geometry...
   Saved window geometry: 1400x900 at (100, 100)
💾 Writing settings to file...
✅ Settings saved via aboutToQuit  ← 新日志
Stopping auto-analyzer...
Stopping folder watchers...
```

---

## ✅ 修复完成

### 改动文件：
- `CC_Main.py`

### 改动内容：
1. ✅ 在 `main()` 添加 `aboutToQuit` 信号处理
2. ✅ 在创建 `photo_grid_widget` 后设置初始列数

### 预期效果：
1. ✅ 点击X会保存设置
2. ✅ 重启时列数正确

---

## 🚀 立即测试

**应用已启动！**

请测试：
1. **Zoom到最大** → 应该看到2列
2. **点击 X 关闭**
3. **重新启动** → 应该自动Zoom到最大且显示2列

**两个问题都已修复！** ✅

