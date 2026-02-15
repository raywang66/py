# 圆角缩略图修复 - 2026年2月14日

## 🐛 问题描述

**之前的实现：**
- 容器（QFrame）有圆角背景色
- 但缩略图图片本身还是直角的
- 效果：看到灰色圆角背景，里面的图片是直角，很突兀

```
╭─────────────╮
│  ┌───────┐  │  ← 圆角背景
│  │ 图片  │  │  ← 但图片是直角！
│  │       │  │
│  └───────┘  │
╰─────────────╯
```

## ✅ 解决方案

**现在的实现：**
- 去掉容器背景色
- 直接对图片QPixmap应用圆角遮罩
- 效果：图片本身就是圆角的

```
╭─────────╮
│ 图片    │  ← 图片本身带圆角
│         │
╰─────────╯
```

## 🔧 技术实现

### 1. 添加圆角遮罩函数

```python
def _apply_rounded_corners(self, pixmap: QPixmap, radius: int = 10) -> QPixmap:
    """Apply rounded corners to a pixmap - macOS Photos style"""
    from PySide6.QtGui import QPainter, QPainterPath
    from PySide6.QtCore import QRectF, Qt as QtCore
    
    # Create a new pixmap with transparency
    rounded = QPixmap(pixmap.size())
    rounded.fill(QtCore.GlobalColor.transparent)
    
    # Create painter
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    # Create rounded rectangle path
    path = QPainterPath()
    rect = QRectF(0, 0, pixmap.width(), pixmap.height())
    path.addRoundedRect(rect, radius, radius)
    
    # Clip to rounded rectangle and draw original pixmap
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    
    return rounded
```

### 2. 移除QLabel背景

**之前：**
```python
self.thumbnail_label.setStyleSheet("""
    QLabel {
        background-color: #f5f5f5;
        border-radius: 10px;
    }
""")
```

**现在：**
```python
self.thumbnail_label.setStyleSheet("background-color: transparent;")
```

### 3. 在所有地方应用圆角

修改了5个位置：

1. **Placeholder（加载占位符）**
```python
pixmap = QPixmap(size, size)
pixmap.fill(QColor(245, 245, 245))
# ... draw loading text ...
rounded_pixmap = self._apply_rounded_corners(pixmap, radius=10)
self.thumbnail_label.setPixmap(rounded_pixmap)
```

2. **缓存命中（从数据库加载）**
```python
data = img.tobytes('raw', 'RGB')
qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
pixmap = QPixmap.fromImage(qimage)
rounded_pixmap = self._apply_rounded_corners(pixmap, radius=10)
self.thumbnail_label.setPixmap(rounded_pixmap)
```

3. **新生成缩略图**
```python
data = img.tobytes('raw', 'RGB')
qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
pixmap = QPixmap.fromImage(qimage)
rounded_pixmap = self._apply_rounded_corners(pixmap, radius=10)
self.thumbnail_label.setPixmap(rounded_pixmap)
```

4. **RAW文件错误处理**
```python
pixmap = QPixmap(size, size)
pixmap.fill(QColor(245, 245, 245))
rounded_pixmap = self._apply_rounded_corners(pixmap, radius=10)
self.thumbnail_label.setPixmap(rounded_pixmap)
```

5. **通用错误处理**
```python
pixmap = QPixmap(size, size)
pixmap.fill(QColor(245, 245, 245))
rounded_pixmap = self._apply_rounded_corners(pixmap, radius=10)
self.thumbnail_label.setPixmap(rounded_pixmap)
```

## 🎨 视觉效果

### 之前（错误）
```
╭───────────────╮  ← 灰色圆角背景
│               │
│   ┌───────┐   │  ← 图片是直角
│   │       │   │
│   │ Photo │   │
│   │       │   │
│   └───────┘   │
│               │
╰───────────────╯
```

### 现在（正确）
```
  ╭─────────╮
  │         │
  │ Photo   │  ← 图片本身圆角
  │         │
  ╰─────────╯
```

## 🔍 技术细节

### QPainterPath 圆角裁剪

1. **创建透明画布**：`rounded.fill(QtCore.GlobalColor.transparent)`
2. **开启抗锯齿**：`painter.setRenderHint(QPainter.RenderHint.Antialiasing)`
3. **创建圆角矩形路径**：`path.addRoundedRect(rect, radius, radius)`
4. **裁剪路径**：`painter.setClipPath(path)`
5. **绘制原图**：`painter.drawPixmap(0, 0, pixmap)`

### 性能考虑

- ✅ 只在显示时裁剪一次
- ✅ 使用硬件加速的QPainter
- ✅ 抗锯齿确保边缘平滑
- ✅ 原始缓存数据不变（不存储圆角版本）

## 📊 修改统计

- **修改文件**：1个（CC_Main.py）
- **添加函数**：1个（_apply_rounded_corners）
- **修改位置**：6处
- **圆角半径**：10px

## ✅ 测试清单

- [x] Placeholder显示圆角
- [x] 从缓存加载的图片显示圆角
- [x] 新生成的缩略图显示圆角
- [x] RAW文件错误时显示圆角占位符
- [x] 通用错误时显示圆角占位符
- [x] 边缘平滑（抗锯齿）
- [x] 选中状态蓝框依然正常显示

## 🎯 结果

现在缩略图**本身就是圆角**的，不再有背景色和图片不匹配的问题！

macOS Photos风格的圆角缩略图实现完美！✨

