# 快速入门指南

## 🚀 5 分钟上手

### 步骤 1: 安装依赖

```bash
cd C:\Users\rwang\lc_sln\py
pip install torch torchvision opencv-python Pillow rawpy numpy scipy matplotlib
```

### 步骤 2: 验证环境

```bash
python test_cuda_setup.py
```

**确认看到**：
```
✅ CUDA可用: True
✅ GPU设备: NVIDIA GeForce RTX 3050 Ti Laptop GPU
✅ SkinColorMatcher导入成功
```

### 步骤 3: 准备图片

需要准备：
1. **参考图** (`reference.jpg`) - 理想肤色的人像照片（JPEG/PNG）
2. **测试图** (`test.ARW`) - 需要调整的 Sony RAW 文件

### 步骤 4: 运行分析

创建文件 `my_analysis.py`:

```python
from skin_color_matcher import SkinColorMatcher

# 初始化工具
matcher = SkinColorMatcher(use_gpu=True)

# 一键分析
adjustments = matcher.analyze(
    reference_path="reference.jpg",  # 替换为你的参考图路径
    test_raw_path="test.ARW",        # 替换为你的 RAW 文件路径
    output_dir="output"              # 结果保存目录
)

# 查看结果
print(f"橙色色相调整: {adjustments.hsl_hue_orange:+d}")
print(f"橙色饱和度调整: {adjustments.hsl_sat_orange:+d}")
```

运行：
```bash
python my_analysis.py
```

### 步骤 5: 应用到 Lightroom

打开 Lightroom Classic，找到你的 RAW 文件：

#### A. HSL 面板调整
1. 进入 `Develop` 模块
2. 展开 `HSL / Color` 面板
3. 按照输出的数值调整：

```
HSL Panel:
├─ Hue (色相)
│  ├─ Orange: +15
│  └─ Red: +12
├─ Saturation (饱和度)
│  ├─ Orange: -20
│  └─ Red: -18
└─ Luminance (亮度)
   ├─ Orange: +10
   └─ Red: +8
```

#### B. Color Grading 调整
1. 展开 `Color Grading` 面板
2. 切换到 `3-Way` 视图
3. 调整色轮：

```
Shadows (阴影):
├─ Hue: 28.5° (拖动色轮到橙色方向)
└─ Saturation: 35.2

Midtones (中间调):
├─ Hue: 32.1°
└─ Saturation: 28.7

Highlights (高光):
├─ Hue: 30.8°
└─ Saturation: 15.3
```

---

## 📊 输出文件说明

运行后会生成以下文件：

```
output/
├── skin_color_analysis.png    # 可视化分析图表
└── (其他临时文件)

skin_color_matcher.log          # 详细日志文件
```

### 分析图表布局

`skin_color_analysis.png` 包含：

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│  参考图像   │  测试图像   │  参考Mask   │  测试Mask   │
├─────────────┼─────────────┼─────────────┼─────────────┤
│  色相分布   │  饱和度分布 │  亮度分布   │  阴影区色相 │
├─────────────┴─────────────┼─────────────┴─────────────┤
│   HSL 调整参数表          │   Color Grading 参数表    │
└───────────────────────────┴───────────────────────────┘
```

---

## 💡 使用技巧

### 技巧 1: 批量处理

如果有多张 RAW 文件需要对标到同一参考图：

```python
from skin_color_matcher import SkinColorMatcher
from pathlib import Path

matcher = SkinColorMatcher(use_gpu=True)

reference = "reference.jpg"
raw_folder = Path("raw_photos")

for raw_file in raw_folder.glob("*.ARW"):
    print(f"处理: {raw_file.name}")
    
    adjustments = matcher.analyze(
        reference_path=reference,
        test_raw_path=raw_file,
        output_dir=f"output/{raw_file.stem}"
    )
    
    print(f"✅ 完成: {raw_file.name}")
```

### 技巧 2: 保存参数为 JSON

```python
import json
from dataclasses import asdict

adjustments = matcher.analyze(...)

# 保存到 JSON 文件
with open("adjustments.json", "w") as f:
    json.dump(asdict(adjustments), f, indent=2)

print("✅ 参数已保存到 adjustments.json")
```

JSON 内容示例：
```json
{
  "hsl_hue_orange": 15,
  "hsl_hue_red": 12,
  "hsl_sat_orange": -20,
  "hsl_sat_red": -18,
  "hsl_lum_orange": 10,
  "hsl_lum_red": 8,
  "shadows_hue": 28.5,
  "shadows_sat": 35.2,
  "midtones_hue": 32.1,
  "midtones_sat": 28.7,
  "highlights_hue": 30.8,
  "highlights_sat": 15.3
}
```

### 技巧 3: 使用 CPU 模式（无 GPU）

```python
# 强制使用 CPU
matcher = SkinColorMatcher(use_gpu=False)

adjustments = matcher.analyze(
    reference_path="reference.jpg",
    test_raw_path="test.ARW",
    output_dir="output_cpu"
)
```

### 技巧 4: 查看详细日志

```python
import logging

# 设置日志级别为 DEBUG
logging.getLogger('SkinColorMatcher').setLevel(logging.DEBUG)

matcher = SkinColorMatcher(use_gpu=True)
# ... 运行分析
```

日志文件 `skin_color_matcher.log` 会包含：
- 每个处理步骤的时间戳
- CUDA 内存使用情况
- 详细的错误堆栈（如果发生）

---

## 🔧 故障排除

### 问题 1: CUDA Out of Memory

**错误信息**:
```
RuntimeError: CUDA out of memory. Tried to allocate 1.50 GiB
```

**解决方案**:
```python
# 方案 A: 降低图像分辨率
from PIL import Image

img = Image.open("large_image.jpg")
img = img.resize((2000, 1333))  # 降到 2K 分辨率
img.save("resized_image.jpg")

# 然后使用 resized_image.jpg

# 方案 B: 使用 CPU 模式
matcher = SkinColorMatcher(use_gpu=False)
```

### 问题 2: 没有检测到皮肤

**错误信息**:
```
ValueError: No skin pixels detected in mask!
```

**原因**: 
- 图片中没有清晰的人脸
- 人脸过小或角度过大
- 光照条件极端

**解决方案**:
- 使用正面、光照均匀的人像照片
- 确保人脸占图片 20% 以上面积
- 检查图片是否模糊或过曝

### 问题 3: rawpy 无法读取文件

**错误信息**:
```
rawpy.LibRawFileUnsupportedError: Unsupported file format
```

**解决方案**:
```bash
# 更新 rawpy 到最新版本
pip install --upgrade rawpy

# 或检查文件是否损坏
# 可以用相机厂商的软件测试打开
```

### 问题 4: 调整参数不明显

**现象**: 在 Lightroom 应用参数后效果不明显

**原因**:
- 参考图与测试图光照差异过大
- 肤质/化妆差异
- 需要结合其他调整

**建议**:
1. 选择光照条件相似的参考图
2. 调整参数 ×0.5 或 ×1.5 试试
3. 结合曝光、对比度等其他调整
4. 使用局部调整画笔精细化

---

## 📖 示例场景

### 场景 1: 婚礼摄影批量调色

```python
from skin_color_matcher import SkinColorMatcher
from pathlib import Path

matcher = SkinColorMatcher(use_gpu=True)

# 使用新娘妆容照作为参考
reference = "bride_reference.jpg"

# 批量处理所有婚礼照片
for raw_file in Path("wedding_photos").glob("*.ARW"):
    adjustments = matcher.analyze(
        reference_path=reference,
        test_raw_path=raw_file,
        output_dir=f"output/wedding/{raw_file.stem}"
    )
```

### 场景 2: 人像修图工作流

```python
matcher = SkinColorMatcher(use_gpu=True)

# 1. 分析肤色
adjustments = matcher.analyze(
    reference_path="ideal_skin_tone.jpg",
    test_raw_path="portrait.ARW",
    output_dir="output"
)

# 2. 保存参数
import json
from dataclasses import asdict

with open("portrait_adjustments.json", "w") as f:
    json.dump(asdict(adjustments), f, indent=2)

# 3. 在 Lightroom 中应用参数
print("✅ 参数已保存，请在 Lightroom 中手动应用")
```

### 场景 3: 产品摄影（模特肤色统一）

```python
matcher = SkinColorMatcher(use_gpu=True)

# 统一品牌标准肤色
brand_reference = "brand_standard_skin.jpg"

for product_photo in Path("product_photos").glob("*.ARW"):
    adjustments = matcher.analyze(
        reference_path=brand_reference,
        test_raw_path=product_photo,
        output_dir=f"output/products/{product_photo.stem}"
    )
```

---

## 🎯 最佳实践

### 1. 选择好的参考图

✅ **推荐**:
- 正面人像，光照均匀
- 肤质清晰，无重度修图
- 色彩准确（来自校准过的显示器）
- 肤色符合目标标准

❌ **避免**:
- 侧脸或角度过大
- 强烈阴影或高光溢出
- 过度磨皮或滤镜
- 色彩偏差（如绿屏反光）

### 2. RAW 文件处理

- **保留原始 RAW**：不要在相机中应用预设
- **关闭降噪**：在 Lightroom 中手动调整
- **统一白平衡**：使用灰卡或色卡
- **拍摄格式**：14-bit RAW（如果相机支持）

### 3. Lightroom 应用技巧

- **逐步调整**：先应用 50% 参数值观察效果
- **局部调整**：结合渐变滤镜和调整画笔
- **保存预设**：将常用参数保存为 Lightroom 预设
- **对比检查**：使用 Before/After 视图验证

### 4. 性能优化

```python
# 一次性加载模型，批量处理
matcher = SkinColorMatcher(use_gpu=True)

raw_files = list(Path("photos").glob("*.ARW"))

for raw_file in raw_files:
    adjustments = matcher.analyze(
        reference_path="reference.jpg",
        test_raw_path=raw_file,
        output_dir=f"output/{raw_file.stem}"
    )
    
    # 清理 GPU 缓存（可选）
    import torch
    torch.cuda.empty_cache()
```

---

## 📞 获取帮助

### 查看文档

- **完整文档**: `README_skin_matcher.md`
- **API 参考**: `API_REFERENCE.md`
- **示例代码**: `skin_matcher_examples.py`
- **测试脚本**: `test_cuda_setup.py`

### 查看日志

```bash
# 实时监控日志
tail -f skin_color_matcher.log  # Linux/Mac

# 或在 Windows PowerShell
Get-Content skin_color_matcher.log -Wait
```

### 调试模式

```python
import logging

# 开启详细日志
logging.basicConfig(level=logging.DEBUG)

matcher = SkinColorMatcher(use_gpu=True)
# ... 运行分析，会输出详细调试信息
```

---

## 🎓 进阶主题

### 自定义统计分析

```python
# 继承并扩展功能
class MyCustomMatcher(SkinColorMatcher):
    def analyze_advanced(self, ref_path, test_path):
        # 调用父类方法
        ref_img = self.load_reference_image(ref_path)
        test_img = self.load_raw_image(test_path)
        
        # 自定义分析
        # ... 你的代码
        
        return custom_results
```

### 集成到自动化工作流

```python
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RAWFileHandler(FileSystemEventHandler):
    def __init__(self, matcher, reference):
        self.matcher = matcher
        self.reference = reference
    
    def on_created(self, event):
        if event.src_path.endswith('.ARW'):
            print(f"检测到新 RAW 文件: {event.src_path}")
            self.matcher.analyze(
                reference_path=self.reference,
                test_raw_path=event.src_path,
                output_dir="auto_output"
            )

# 监控文件夹
matcher = SkinColorMatcher(use_gpu=True)
handler = RAWFileHandler(matcher, "reference.jpg")

observer = Observer()
observer.schedule(handler, path="watched_folder", recursive=False)
observer.start()

print("📂 监控文件夹中，等待 RAW 文件...")
```

---

**🎉 开始使用吧！**

有任何问题，请查看完整文档或查看日志文件。

