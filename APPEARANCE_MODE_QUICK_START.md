# ChromaCloud Appearance Mode - Quick Start Guide

## 🎨 如何使用新的外观模式

### 启动应用
```bash
python CC_Main.py
```

### 切换主题

#### 方法 1: 使用菜单
1. 点击顶部菜单栏的 **View**
2. 选择 **🎨 Appearance**
3. 选择你想要的模式：
   - **💻 Follow System** - 自动跟随 Windows 11 系统主题
   - **☀️ Light** - 始终使用浅色模式
   - **🌙 Dark** - 始终使用深色模式

#### 当前选中的模式会显示 ✓ 勾选标记

---

## 🪟 Windows 11 特色功能

### 标题栏自动匹配
- **深色模式** → 黑色标题栏
- **浅色模式** → 白色标题栏
- 完美融入 Windows 11 风格

### 系统主题检测
- 应用会自动读取你的 Windows 11 主题设置
- 选择 "Follow System" 模式后，启动时自动匹配

---

## 💾 自动保存

### 退出时自动保存
- 直接点击 **X** 关闭窗口
- 所有设置（包括外观模式）会自动保存
- 下次启动时恢复上次的状态

### 手动保存（可选）
- 按 **Ctrl+S**
- 或者 **File → Save Settings Now**

---

## 🔄 从旧版本升级

### 自动迁移
如果你之前使用过 ChromaCloud：
- 旧的 `dark_mode` 设置会自动转换
- `dark_mode=true` → `appearance_mode=dark`
- `dark_mode=false` → `appearance_mode=light`

### 日志确认
启动时检查日志，会看到：
```
🔄 Migrated dark_mode=True to appearance_mode=dark
```

---

## 🎯 推荐使用方式

### Windows 11 用户
1. 选择 **💻 Follow System** 模式（默认）
2. 在 Windows 设置中切换深色/浅色主题
3. 重启 ChromaCloud → 自动匹配系统主题

### macOS 用户（即将测试）
1. 选择 **💻 Follow System** 模式
2. 在 System Preferences → General → Appearance 切换
3. 重启 ChromaCloud → 自动匹配系统主题

### 固定主题用户
- 如果你总是喜欢深色或浅色
- 选择 **🌙 Dark** 或 **☀️ Light**
- 不受系统设置影响

---

## ⚙️ 技术细节

### 配置文件位置
```
C:\Users\rwang\lc_sln\py\chromacloud_settings.json
```

### 配置格式
```json
{
  "ui": {
    "appearance_mode": "system"  // "system", "light", or "dark"
  }
}
```

---

## 🐛 故障排除

### 问题：主题没有自动切换
**解决方案：**
1. 检查是否选择了 "Follow System" 模式
2. 重启应用以应用系统主题
3. 检查 Windows 11 设置：
   ```
   Settings → Personalization → Colors → Choose your mode
   ```

### 问题：退出时设置没有保存
**解决方案：**
1. 手动按 **Ctrl+S** 保存
2. 检查日志文件 `chromacloud.log`
3. 确认配置文件权限正常

### 问题：标题栏颜色不匹配
**解决方案：**
- 这是 Windows 11 特有功能
- 需要 Windows 10 Build 19041 或更高版本
- 检查日志中是否有错误信息

---

## 📝 更新日志

### v1.3 - 2026-02-15
- ✅ 新增三种外观模式（System/Light/Dark）
- ✅ 自动检测系统主题（Windows 11 & macOS）
- ✅ Windows 11 标题栏颜色同步
- ✅ 退出时自动保存设置
- ✅ 旧设置自动迁移
- ✅ 滚动条深色模式修复

---

**享受原生级别的深色/浅色模式体验！** 🚀

