# Statistics Window Dark Mode Support

## Date: February 15, 2026

## ✅ 完成内容

Statistics Window 现在完全支持深色/浅色模式，自动跟随主窗口的外观设置。

---

## 🎨 功能特性

### 1. **自动主题匹配**
   - Statistics Window 打开时自动检测主窗口的当前主题
   - 包括 "Follow System" 模式的自动检测
   - 完美匹配主窗口的外观

### 2. **深色模式样式**
   - **背景**: 纯黑 (`#000000`)
   - **文本**: 白色 (`#ffffff`)
   - **标签页**: 深灰选中标签，黑色背景
   - **按钮**: 蓝色高亮 (`#0a84ff`)
   - **图表背景**: 深灰 (`#0a0a0a`)

### 3. **浅色模式样式**
   - **背景**: 纯白 (`#ffffff`)
   - **文本**: 深灰 (`#333333`)
   - **标签页**: 浅灰选中标签，白色背景
   - **按钮**: 蓝色 (`#007AFF`)
   - **图表背景**: 浅灰 (`#FAFAFA`)

---

## 🔧 技术实现

### 修改的文件

#### 1. **CC_StatisticsWindow.py**

**构造函数更新：**
```python
def __init__(self, album_name: str, stats_data: List[Dict], is_dark: bool = False):
    super().__init__()
    self.album_name = album_name
    self.stats_data = stats_data
    self.is_dark = is_dark  # 新增：保存主题状态
```

**新增辅助方法：**
```python
def _get_plot_bg_color(self):
    """Get plot background color based on theme"""
    return '#0a0a0a' if self.is_dark else '#FAFAFA'

def _get_text_color(self):
    """Get text color based on theme"""
    return '#ffffff' if self.is_dark else '#333333'

def _get_grid_color(self):
    """Get grid color based on theme"""
    return '#2c2c2c' if self.is_dark else '#DDDDDD'
```

**重写 _apply_theme() 方法：**
- 支持深色和浅色两种完整样式
- 自动应用到所有 UI 组件

**更新 MplCanvas 类：**
```python
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=8, height=6, dpi=100, is_dark=False):
        facecolor = '#000000' if is_dark else 'white'
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor=facecolor)
        self.axes = fig.add_subplot(111, facecolor=facecolor)
        
        # 深色模式下设置坐标轴颜色
        if is_dark:
            self.axes.tick_params(colors='white', which='both')
            self.axes.xaxis.label.set_color('white')
            self.axes.yaxis.label.set_color('white')
            self.axes.title.set_color('white')
            for spine in self.axes.spines.values():
                spine.set_edgecolor('#2c2c2c')
```

**更新所有图表创建：**
- 所有 `MplCanvas()` 调用都传递 `is_dark=self.is_dark`
- 所有 `ax.set_facecolor()` 使用 `self._get_plot_bg_color()`

#### 2. **CC_Main.py**

**新增辅助方法：**
```python
def _is_current_theme_dark(self) -> bool:
    """Get current effective dark mode state (considering system mode)"""
    if self.appearance_mode == 'system':
        return self._is_system_dark_mode()
    elif self.appearance_mode == 'dark':
        return True
    else:  # 'light'
        return False
```

**更新 Statistics Window 创建：**
```python
# 确定当前主题状态
is_dark = self._is_current_theme_dark()

from CC_StatisticsWindow import CC_StatisticsWindow
stats_window = CC_StatisticsWindow(data['name'], detailed_stats, is_dark=is_dark)
stats_window.show()
```

---

## 🎯 视觉对比

### 浅色模式
- ✅ 纯白背景
- ✅ 深色文字 (#333333)
- ✅ 浅灰图表背景 (#FAFAFA)
- ✅ 蓝色强调色 (#007AFF)

### 深色模式
- ✅ 纯黑背景 (#000000)
- ✅ 白色文字 (#ffffff)
- ✅ 深灰图表背景 (#0a0a0a)
- ✅ 亮蓝强调色 (#0a84ff)

---

## 📊 支持的图表类型

所有图表类型都完全支持深色/浅色模式：

1. **📈 Overview Tab**
   - 统计摘要卡片
   - 自适应背景和文字颜色

2. **🎨 Hue Distribution**
   - 色调分布直方图
   - 深色模式下白色坐标轴和文字

3. **💡 Lightness Distribution**
   - 亮度分布堆叠条形图
   - 自动调整图表背景

4. **🎨 Hue Comparison**
   - 色调分类对比图
   - 深色模式下清晰可见

5. **💧 Saturation Comparison**
   - 饱和度分类对比图
   - 自适应主题颜色

6. **🔀 3D HSL Distribution**
   - 3D散点图
   - 深色背景下更加醒目

---

## ✨ 用户体验

### 打开 Statistics Window
1. 在主窗口选择任意模式（System/Light/Dark）
2. 右键点击相册 → "View Statistics"
3. Statistics Window 自动匹配当前主题

### 切换主题
- 切换主题后，需要重新打开 Statistics Window
- 新打开的窗口会使用新的主题

---

## 🧪 测试场景

### ✅ 已测试
- [x] 浅色模式下打开 Statistics Window
- [x] 深色模式下打开 Statistics Window
- [x] Follow System 模式自动检测
- [x] 所有图表标签页正确渲染
- [x] Matplotlib 图表背景正确
- [x] 坐标轴和文字在深色模式下可见

---

## 🎨 设计原则

遵循 **macOS Photos** 应用的设计语言：

1. **极简主义** - 干净的背景，清晰的对比
2. **一致性** - 与主窗口完美匹配
3. **可读性** - 深色模式下文字清晰可见
4. **专业性** - 图表和数据可视化专业美观

---

## 📝 代码改动总结

### 新增代码
- `_get_plot_bg_color()` - 获取图表背景色
- `_get_text_color()` - 获取文本颜色
- `_get_grid_color()` - 获取网格颜色
- `_is_current_theme_dark()` - 判断当前有效主题

### 修改代码
- `CC_StatisticsWindow.__init__()` - 接受 `is_dark` 参数
- `_apply_theme()` - 支持深色和浅色模式
- `MplCanvas.__init__()` - 接受并应用 `is_dark`
- 所有图表创建 - 传递主题参数

### 批量替换
- `MplCanvas(parent_tab, ...)` → 添加 `is_dark=self.is_dark`
- `ax.set_facecolor('#FAFAFA')` → `ax.set_facecolor(self._get_plot_bg_color())`

---

## 🚀 后续优化

可能的未来改进：

- [ ] 实时主题切换（不重新打开窗口）
- [ ] 自定义主题颜色
- [ ] 图表导出时保持主题
- [ ] 更多图表类型支持

---

## ✅ 完成状态

**Statistics Window 深色模式支持已完成！**

- ✅ 完全支持深色/浅色模式
- ✅ 自动跟随主窗口设置
- ✅ 所有图表类型适配
- ✅ Matplotlib 图表完美渲染
- ✅ 文字和UI元素清晰可见

---

**现在 ChromaCloud 的所有窗口都支持深色模式了！** 🎉

