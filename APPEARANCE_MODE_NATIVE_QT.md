# Native Qt Appearance Mode Implementation

## Date: February 15, 2026

## Overview
ChromaCloud现在使用**PySide6原生的Palette系统**来实现浅色/深色模式，替代了之前的手动toggle实现。

---

## ✨ 新功能：三种外观模式

### 1. **💻 Follow System (跟随系统)**
   - 自动检测操作系统的深色/浅色模式设置
   - Windows 11: 读取注册表 `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme`
   - macOS: 使用 `defaults read -g AppleInterfaceStyle` 命令
   - 启动时自动应用系统主题
   - **这是默认模式**

### 2. **☀️ Light (浅色模式)**
   - 始终使用浅色主题
   - 不受系统设置影响
   - macOS Photos 风格的白色背景

### 3. **🌙 Dark (深色模式)**
   - 始终使用深色主题
   - 不受系统设置影响
   - 纯黑背景 (#000000)，符合 macOS Big Sur/Monterey 设计

---

## 🎯 UI 更新

### View Menu (查看菜单)
```
View
  └─ 🎨 Appearance
       ├─ 💻 Follow System  [✓]
       ├─ ☀️ Light
       └─ 🌙 Dark
```

- 使用 **QActionGroup** 实现单选（radio button 风格）
- 当前模式会显示勾选标记
- 切换立即生效，无需重启

---

## 🔧 技术实现

### 核心变更

#### 1. **CC_Settings.py**
- ✅ `dark_mode: bool` → `appearance_mode: str`
- ✅ 新增 `get_appearance_mode()` / `set_appearance_mode(mode)`
- ✅ 自动迁移旧设置：`dark_mode=True` → `'dark'`, `dark_mode=False` → `'light'`

#### 2. **CC_Main.py**

**新增方法：**
```python
def _apply_theme(self):
    """应用主题 - 根据 appearance_mode 自动决定深色/浅色"""
    if self.appearance_mode == 'system':
        is_dark = self._is_system_dark_mode()
    elif self.appearance_mode == 'dark':
        is_dark = True
    else:  # 'light'
        is_dark = False
    
    # 使用 Qt 原生 QPalette 系统
    app = QApplication.instance()
    app.setStyle("Fusion")
    palette = QPalette()
    # ... 设置颜色 ...
    app.setPalette(palette)

def _is_system_dark_mode(self) -> bool:
    """检测系统是否在深色模式"""
    # Windows: 读取注册表
    # macOS: 运行 defaults 命令
    
def _update_windows_title_bar(self, is_dark: bool):
    """Windows 11 特殊处理：更新标题栏颜色"""
```

**替换的方法：**
- ❌ `_toggle_theme()` (删除)
- ✅ `_set_appearance_mode(mode: str)` (新增)
- ✅ `_update_theme_menu_text()` (新增，更新菜单勾选状态)

---

## 🪟 Windows 11 特殊处理

### 标题栏颜色同步
```python
# 使用 DWM API 设置标题栏颜色
windll.dwmapi.DwmSetWindowAttribute(
    hwnd, 
    DWMWA_USE_IMMERSIVE_DARK_MODE,  # 20
    byref(c_int(1 if is_dark else 0)), 
    4
)
```

- 深色模式：标题栏变黑
- 浅色模式：标题栏变白
- 完美匹配 Windows 11 系统风格

---

## 📝 配置文件格式

### chromacloud_settings.json
```json
{
  "window": {
    "x": 100,
    "y": 100,
    "width": 1400,
    "height": 900,
    "maximized": false
  },
  "ui": {
    "appearance_mode": "system",  // "system" | "light" | "dark"
    "zoom_level": 200
  },
  "navigation": {
    "last_album_id": 2,
    "selected_item_type": "folder"
  }
}
```

---

## 🔄 自动迁移逻辑

### 旧版本兼容性
如果检测到旧的 `dark_mode` 字段：
```json
{
  "ui": {
    "dark_mode": true  // 旧格式
  }
}
```

自动转换为：
```json
{
  "ui": {
    "appearance_mode": "dark"  // 新格式
  }
}
```

日志输出：
```
🔄 Migrated dark_mode=True to appearance_mode=dark
```

---

## 🎨 滚动条修复

### Dark Mode 滚动条
之前的问题：
- ❌ 白色网格背景 + 黑色滑块

现在：
- ✅ 纯黑背景 (`#000000`) + 浅灰滑块 (`#b0b0b0`)

```css
QScrollBar:vertical {
    background: #000000;  /* 纯黑背景 */
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #b0b0b0;  /* 浅灰滑块 */
    border-radius: 6px;
}
```

---

## ✅ 退出时保存状态

### 自动保存的内容
1. **窗口位置和大小**
2. **外观模式** (`appearance_mode`)
3. **缩放级别** (`zoom_level`)
4. **当前相册/文件夹** (`last_album_id`, `last_folder_path`)

### 保存时机
- ❌ 点击 X 关闭窗口 → **现在会自动保存**
- ✅ File → Save Settings Now (Ctrl+S) → 立即保存

---

## 🚀 使用方法

### 1. 启动应用
```bash
python CC_Main.py
```

### 2. 切换外观模式
**方式一：菜单**
```
View → Appearance → 选择一个模式
```

**方式二：首次启动**
- 默认使用 `Follow System` 模式
- 自动匹配你的 Windows 11 系统主题

### 3. 退出时自动保存
- 关闭窗口 → 自动保存所有设置
- 下次启动 → 恢复上次的外观模式

---

## 🧪 测试步骤

### Windows 11 测试
1. ✅ **Follow System 模式**
   - 将 Windows 11 设置为深色模式
   - 启动 ChromaCloud → 应该自动使用深色主题
   - 将 Windows 11 切换为浅色模式
   - 重启 ChromaCloud → 应该自动使用浅色主题

2. ✅ **Light 模式**
   - 选择 View → Appearance → Light
   - 应该立即切换为浅色主题
   - 关闭并重启 → 依然是浅色主题

3. ✅ **Dark 模式**
   - 选择 View → Appearance → Dark
   - 应该立即切换为深色主题
   - 标题栏应该变黑
   - 滚动条应该是黑色背景 + 白色滑块

### macOS 测试
```bash
# 检查系统深色模式
defaults read -g AppleInterfaceStyle
# 输出 "Dark" 或 错误（表示浅色模式）

# 切换系统主题
System Preferences → General → Appearance
```

---

## 📊 对比：旧实现 vs 新实现

| 特性 | 旧实现 (Toggle) | 新实现 (Native Qt) |
|------|----------------|-------------------|
| 模式数量 | 2 (Light/Dark) | 3 (System/Light/Dark) |
| 系统集成 | ❌ 无 | ✅ 自动检测系统主题 |
| 菜单风格 | Toggle 按钮 | Radio 单选组 |
| Windows 标题栏 | ⚠️ 手动设置 | ✅ 自动同步 |
| 配置格式 | `dark_mode: bool` | `appearance_mode: str` |
| 兼容性 | - | ✅ 自动迁移旧设置 |

---

## 🎯 优势

1. **更符合原生体验**
   - macOS 用户期望应用跟随系统主题
   - Windows 11 用户期望应用匹配系统主题

2. **灵活性**
   - 用户可以选择始终使用某个主题
   - 或者跟随系统自动切换

3. **代码简洁**
   - 使用 Qt 原生 API
   - 减少手动管理状态

4. **跨平台一致**
   - Windows 和 macOS 行为一致
   - 自动适配各平台的主题检测方式

---

## 🔮 未来改进

- [ ] 监听系统主题变化事件（运行时自动切换）
- [ ] 添加 "Auto" 定时切换（白天浅色，晚上深色）
- [ ] 自定义颜色方案
- [ ] 主题预览（切换前预览效果）

---

## 📖 相关文档
- `CC_Settings.py` - 设置管理器
- `CC_Main.py` - 主应用窗口
- `chromacloud_settings.json` - 配置文件

---

## ✅ 完成状态
- [x] 三种外观模式实现
- [x] 系统主题检测（Windows 11 & macOS）
- [x] Windows 11 标题栏同步
- [x] 滚动条深色模式修复
- [x] 退出时自动保存
- [x] 旧设置自动迁移
- [x] 菜单勾选状态显示

---

**现在您可以享受原生级别的深色/浅色模式体验！** 🎉

