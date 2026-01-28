# API 参考文档

## SkinColorMatcher 类

### 初始化

```python
SkinColorMatcher(use_gpu: bool = True, model_path: Optional[str] = None)
```

**参数**：
- `use_gpu` (bool): 启用 GPU 加速，默认 True
- `model_path` (str, optional): 自定义 Face Parsing 模型路径

**属性**：
- `device` (torch.device): 计算设备（cuda 或 cpu）
- `face_parser` (torch.nn.Module): 人脸分割模型
- `logger` (logging.Logger): 日志记录器

**示例**：
```python
# GPU 模式
matcher = SkinColorMatcher(use_gpu=True)

# CPU 模式
matcher = SkinColorMatcher(use_gpu=False)

# 自定义模型
matcher = SkinColorMatcher(use_gpu=True, model_path="path/to/model.pth")
```

---

### 核心方法

#### analyze()

```python
analyze(
    reference_path: Union[str, Path],
    test_raw_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None
) -> LightroomAdjustments
```

**功能**: 完整的分析流程（一键式）

**参数**：
- `reference_path`: 参考图像路径（JPEG/PNG）
- `test_raw_path`: 测试图像路径（Sony .ARW）
- `output_dir`: 输出目录（可选）

**返回**：
- `LightroomAdjustments`: 调整参数对象

**异常**：
- `FileNotFoundError`: 文件不存在
- `ValueError`: 无皮肤像素检测
- `RuntimeError`: CUDA 错误

**示例**：
```python
adjustments = matcher.analyze(
    reference_path="ref.jpg",
    test_raw_path="test.ARW",
    output_dir="output"
)
```

---

#### load_reference_image()

```python
load_reference_image(image_path: Union[str, Path]) -> np.ndarray
```

**功能**: 加载 JPEG/PNG 参考图像

**参数**：
- `image_path`: 图像文件路径

**返回**：
- `np.ndarray`: RGB 图像数组 (H, W, 3)，范围 [0, 1]

**示例**：
```python
ref_img = matcher.load_reference_image("reference.jpg")
print(ref_img.shape)  # (1080, 1920, 3)
print(ref_img.dtype)  # float32
```

---

#### load_raw_image()

```python
load_raw_image(
    raw_path: Union[str, Path],
    apply_gamma: bool = True
) -> np.ndarray
```

**功能**: 加载并处理 Sony .ARW RAW 文件

**参数**：
- `raw_path`: RAW 文件路径
- `apply_gamma`: 应用 Gamma 2.2 校正（强烈推荐）

**返回**：
- `np.ndarray`: RGB 图像数组 (H, W, 3)，范围 [0, 1]

**重要**: 
- 使用 16 位精度处理
- `apply_gamma=True` 确保与 JPEG 亮度对齐
- 禁用自动亮度调整

**示例**：
```python
# 标准处理（推荐）
raw_img = matcher.load_raw_image("test.ARW", apply_gamma=True)

# 线性数据（高级用法）
raw_linear = matcher.load_raw_image("test.ARW", apply_gamma=False)
```

---

#### extract_skin_mask()

```python
@torch.no_grad()
extract_skin_mask(image: np.ndarray) -> np.ndarray
```

**功能**: 提取精确的皮肤区域 mask

**参数**：
- `image`: RGB 图像数组 (H, W, 3)

**返回**：
- `np.ndarray`: 布尔 mask (H, W)

**特性**：
- GPU 加速推理
- 排除眼睛、嘴唇、头发
- 形态学后处理
- 自动 fallback 机制

**示例**：
```python
skin_mask = matcher.extract_skin_mask(image)
print(f"皮肤像素: {skin_mask.sum()}")

# 可视化
import matplotlib.pyplot as plt
plt.imshow(skin_mask, cmap='gray')
plt.show()
```

---

#### rgb_to_hsl()

```python
rgb_to_hsl(rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]
```

**功能**: RGB 转 HSL 色彩空间

**参数**：
- `rgb`: RGB 数组 (..., 3)，范围 [0, 1]

**返回**：
- `h`: 色相，范围 [0, 360]（度）
- `s`: 饱和度，范围 [0, 1]
- `l`: 亮度，范围 [0, 1]

**性能**: 高性能 NumPy 向量化运算

**示例**：
```python
skin_pixels = image[mask]  # (N, 3)
h, s, l = matcher.rgb_to_hsl(skin_pixels)

print(f"平均色相: {np.mean(h):.1f}°")
print(f"平均饱和度: {np.mean(s):.3f}")
```

---

#### compute_color_statistics()

```python
compute_color_statistics(
    image: np.ndarray,
    mask: np.ndarray
) -> ColorStats
```

**功能**: 计算 mask 区域的色彩统计数据

**参数**：
- `image`: RGB 图像数组 (H, W, 3)
- `mask`: 布尔 mask (H, W)

**返回**：
- `ColorStats`: 统计数据对象

**统计指标**：
- 均值、标准差、中位数（H, S, L）
- 阴影区域统计（L < 20%）
- 总像素数

**示例**：
```python
stats = matcher.compute_color_statistics(image, mask)

print(f"色相均值: {stats.h_mean:.1f}°")
print(f"饱和度均值: {stats.s_mean:.3f}")
print(f"亮度均值: {stats.l_mean:.3f}")
print(f"阴影色相: {stats.shadow_h_mean:.1f}°")
print(f"总像素: {stats.total_pixels}")
```

---

#### compute_lightroom_adjustments()

```python
compute_lightroom_adjustments(
    ref_stats: ColorStats,
    test_stats: ColorStats
) -> LightroomAdjustments
```

**功能**: 计算 Lightroom 调整参数

**参数**：
- `ref_stats`: 参考图统计数据
- `test_stats`: 测试图统计数据

**返回**：
- `LightroomAdjustments`: 调整参数对象

**映射逻辑**：
- HSL: 统计差异 → 滑块值（-100 到 +100）
- Color Grading: 色相/饱和度 → 色轮参数

**示例**：
```python
adj = matcher.compute_lightroom_adjustments(ref_stats, test_stats)

print(f"橙色色相: {adj.hsl_hue_orange:+d}")
print(f"橙色饱和度: {adj.hsl_sat_orange:+d}")
print(f"阴影色相: {adj.shadows_hue:.1f}°")
```

---

#### visualize_results()

```python
visualize_results(
    ref_img: np.ndarray,
    test_img: np.ndarray,
    ref_mask: np.ndarray,
    test_mask: np.ndarray,
    ref_stats: ColorStats,
    test_stats: ColorStats,
    adjustments: LightroomAdjustments,
    save_path: Optional[str] = None
)
```

**功能**: 生成综合可视化分析图

**参数**：
- `ref_img`: 参考图像
- `test_img`: 测试图像
- `ref_mask`: 参考 mask
- `test_mask`: 测试 mask
- `ref_stats`: 参考统计
- `test_stats`: 测试统计
- `adjustments`: 调整参数
- `save_path`: 保存路径（可选）

**输出**: 3×4 网格布局的分析图表

**示例**：
```python
matcher.visualize_results(
    ref_img, test_img,
    ref_mask, test_mask,
    ref_stats, test_stats,
    adjustments,
    save_path="analysis.png"
)
```

---

## 数据类

### ColorStats

```python
@dataclass
class ColorStats:
    h_mean: float          # 色相均值（0-360°）
    s_mean: float          # 饱和度均值（0-1）
    l_mean: float          # 亮度均值（0-1）
    h_std: float           # 色相标准差
    s_std: float           # 饱和度标准差
    l_std: float           # 亮度标准差
    h_median: float        # 色相中位数
    s_median: float        # 饱和度中位数
    l_median: float        # 亮度中位数
    shadow_h_mean: float   # 阴影区色相均值
    shadow_s_mean: float   # 阴影区饱和度均值
    total_pixels: int      # 总像素数
```

**示例**：
```python
stats = ColorStats(
    h_mean=32.5, s_mean=0.342, l_mean=0.567,
    h_std=8.2, s_std=0.089, l_std=0.124,
    h_median=31.8, s_median=0.335, l_median=0.559,
    shadow_h_mean=28.3, shadow_s_mean=0.298,
    total_pixels=125847
)

print(stats.h_mean)  # 32.5
```

---

### LightroomAdjustments

```python
@dataclass
class LightroomAdjustments:
    # HSL 面板（-100 到 +100）
    hsl_hue_orange: int
    hsl_hue_red: int
    hsl_sat_orange: int
    hsl_sat_red: int
    hsl_lum_orange: int
    hsl_lum_red: int
    
    # Color Grading
    shadows_hue: float      # 0-360°
    shadows_sat: float      # 0-100
    midtones_hue: float
    midtones_sat: float
    highlights_hue: float
    highlights_sat: float
```

**示例**：
```python
adj = LightroomAdjustments(
    hsl_hue_orange=15, hsl_hue_red=12,
    hsl_sat_orange=-20, hsl_sat_red=-18,
    hsl_lum_orange=10, hsl_lum_red=8,
    shadows_hue=28.5, shadows_sat=35.2,
    midtones_hue=32.1, midtones_sat=28.7,
    highlights_hue=30.8, highlights_sat=15.3
)

# 转换为字典
from dataclasses import asdict
adj_dict = asdict(adj)

# 保存为 JSON
import json
with open("adjustments.json", "w") as f:
    json.dump(adj_dict, f, indent=2)
```

---

## 常量定义

### 皮肤色调范围

```python
SKIN_HUE_MIN = 0    # 皮肤色相最小值（度）
SKIN_HUE_MAX = 50   # 皮肤色相最大值（度）
```

### 阴影阈值

```python
SHADOW_THRESHOLD = 0.20  # 亮度 < 20% 定义为阴影区域
```

### Face Parsing 类别

```python
# 皮肤类别（保留）
SKIN_CLASSES = [1, 2, 3, 10, 11, 12, 13]
# 1: 面部皮肤, 2: 左耳, 3: 右耳
# 10-13: 脖子等其他皮肤区域

# 排除类别
EXCLUDE_CLASSES = [4, 5, 6, 7, 8, 9]
# 4: 左眼, 5: 右眼, 6: 眉毛
# 7: 鼻子, 8: 嘴巴, 9: 嘴唇
```

---

## 异常处理

### 常见异常

| 异常类型 | 触发条件 | 处理建议 |
|----------|----------|----------|
| `FileNotFoundError` | 图像文件不存在 | 检查文件路径 |
| `ValueError` | 无皮肤像素检测 | 使用更清晰的人像照片 |
| `RuntimeError` | CUDA OOM | 降低图像分辨率或使用 CPU |
| `rawpy.LibRawError` | RAW 文件损坏 | 重新拍摄或修复文件 |

### 异常捕获示例

```python
try:
    adjustments = matcher.analyze(
        reference_path="ref.jpg",
        test_raw_path="test.ARW"
    )
except FileNotFoundError as e:
    print(f"文件未找到: {e}")
except ValueError as e:
    print(f"数据无效: {e}")
except RuntimeError as e:
    print(f"运行时错误: {e}")
    # Fallback to CPU
    matcher_cpu = SkinColorMatcher(use_gpu=False)
    adjustments = matcher_cpu.analyze(...)
```

---

## 日志系统

### 日志级别

- `INFO`: 正常处理流程
- `WARNING`: 警告信息（如 CUDA 不可用）
- `ERROR`: 错误信息（含堆栈）

### 日志配置

```python
import logging

# 修改日志级别
logging.getLogger('SkinColorMatcher').setLevel(logging.DEBUG)

# 添加文件处理器
fh = logging.FileHandler('custom.log')
logging.getLogger('SkinColorMatcher').addHandler(fh)
```

### 日志示例

```
2026-01-19 20:41:25,735 - SkinColorMatcher - INFO - Device configured: cuda
2026-01-19 20:41:25,736 - SkinColorMatcher - INFO - Loading face parsing model...
2026-01-19 20:41:26,124 - SkinColorMatcher - INFO - Loading reference image: ref.jpg
2026-01-19 20:41:27,358 - SkinColorMatcher - INFO - Applying Gamma 2.2 correction
2026-01-19 20:41:28,456 - SkinColorMatcher - INFO - CUDA Memory allocated: 156.78 MB
2026-01-19 20:41:29,234 - SkinColorMatcher - INFO - Skin mask extracted: 125847 pixels
```

---

## 性能优化

### GPU 内存管理

```python
# 清理 CUDA 缓存
torch.cuda.empty_cache()

# 查看内存使用
allocated = torch.cuda.memory_allocated(0) / 1e6
print(f"已分配: {allocated:.2f} MB")

# 使用上下文管理器
with torch.no_grad():
    result = model(input_tensor)
```

### 批处理优化

```python
# 预加载模型一次
matcher = SkinColorMatcher(use_gpu=True)

# 批量处理
for raw_file in raw_files:
    adj = matcher.analyze(reference, raw_file, output_dir)
    # 模型保持在内存中，无需重复加载
```

### 图像尺寸建议

| 用途 | 推荐尺寸 | 显存占用 |
|------|----------|----------|
| 快速预览 | 1920×1080 | ~200 MB |
| 标准处理 | 4000×3000 | ~800 MB |
| 高精度 | 6000×4000 | ~1.5 GB |

---

## 版本兼容性

### Python 版本

- **推荐**: Python 3.8+
- **测试**: Python 3.12

### PyTorch 版本

- **最低**: 2.0.0
- **推荐**: 2.7.1+cu128
- **CUDA**: 12.8

### 依赖版本矩阵

| 库 | 最低版本 | 推荐版本 | 备注 |
|----|----------|----------|------|
| torch | 2.0.0 | 2.7.1 | CUDA 版本 |
| numpy | 1.24.0 | 2.0.2 | - |
| opencv-python | 4.8.0 | 4.13.0 | - |
| rawpy | 0.18.0 | 0.25.1 | - |
| scipy | 1.11.0 | 1.14.1 | - |
| matplotlib | 3.7.0 | 3.9.2 | - |

---

## 单元测试

### 测试 GPU 配置

```python
python test_cuda_setup.py
```

### 测试核心功能

```python
import unittest
from skin_color_matcher import SkinColorMatcher
import numpy as np

class TestSkinColorMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = SkinColorMatcher(use_gpu=False)
    
    def test_rgb_to_hsl(self):
        rgb = np.array([[[1.0, 0.0, 0.0]]])  # 纯红色
        h, s, l = self.matcher.rgb_to_hsl(rgb)
        self.assertAlmostEqual(h[0, 0], 0.0)  # 红色 = 0°
        self.assertAlmostEqual(s[0, 0], 1.0)  # 饱和度 = 1
    
    def test_device_setup(self):
        self.assertIn(str(self.matcher.device), ['cpu', 'cuda'])

if __name__ == '__main__':
    unittest.main()
```

---

## 扩展开发

### 自定义统计指标

```python
class CustomSkinColorMatcher(SkinColorMatcher):
    def compute_custom_metrics(self, image, mask):
        """计算自定义指标"""
        pixels = image[mask]
        h, s, l = self.rgb_to_hsl(pixels)
        
        # 计算偏度和峰度
        from scipy.stats import skew, kurtosis
        h_skew = skew(h)
        h_kurt = kurtosis(h)
        
        return {
            'hue_skewness': h_skew,
            'hue_kurtosis': h_kurt
        }
```

### 自定义可视化

```python
def custom_visualization(self, stats):
    """自定义可视化"""
    import seaborn as sns
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.kdeplot(data=h, ax=ax, shade=True)
    ax.set_title('Skin Tone Hue Distribution (KDE)')
    plt.show()
```

---

## 命令行接口（CLI）

### 创建 CLI 包装器

```python
# skin_matcher_cli.py
import argparse
from skin_color_matcher import SkinColorMatcher

def main():
    parser = argparse.ArgumentParser(description='Skin Color Matcher')
    parser.add_argument('--reference', required=True, help='Reference image')
    parser.add_argument('--test', required=True, help='Test RAW file')
    parser.add_argument('--output', default='output', help='Output directory')
    parser.add_argument('--cpu', action='store_true', help='Use CPU mode')
    
    args = parser.parse_args()
    
    matcher = SkinColorMatcher(use_gpu=not args.cpu)
    adjustments = matcher.analyze(
        reference_path=args.reference,
        test_raw_path=args.test,
        output_dir=args.output
    )
    
    print(f"✅ Analysis complete! Check {args.output}/")

if __name__ == '__main__':
    main()
```

### 使用 CLI

```bash
python skin_matcher_cli.py \
    --reference reference.jpg \
    --test test.ARW \
    --output results/
```

---

**更新时间**: 2026-01-19  
**版本**: 1.0.0

