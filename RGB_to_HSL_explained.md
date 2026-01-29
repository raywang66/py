# RGB 到 HSL 转换算法详解

## 概述

对于每个像素的 RGB 值（Red, Green, Blue），我们将其转换为 HSL 色彩空间：
- **H (Hue)**: 色相 - 表示颜色类型（0-360度）
- **S (Saturation)**: 饱和度 - 表示颜色的纯度（0-1）
- **L (Lightness)**: 亮度 - 表示颜色的明暗（0-1）

---

## 算法步骤

### 前提条件
输入：RGB 值，范围 [0, 1]（已归一化）
- R = Red / 255
- G = Green / 255  
- B = Blue / 255

---

### 步骤 1: 计算最大值、最小值和差值

```python
max_c = max(R, G, B)    # 最大颜色分量
min_c = min(R, G, B)    # 最小颜色分量
delta = max_c - min_c   # 色差（chroma）
```

**例子**：
```
RGB = (0.8, 0.5, 0.3)
max_c = 0.8 (红色最大)
min_c = 0.3 (蓝色最小)
delta = 0.5
```

---

### 步骤 2: 计算亮度 (Lightness)

**公式**：
```python
L = (max_c + min_c) / 2
```

**含义**：亮度是最大值和最小值的平均值
- L = 0: 纯黑色
- L = 0.5: 中等亮度（纯色）
- L = 1: 纯白色

**例子**：
```
L = (0.8 + 0.3) / 2 = 0.55
```

---

### 步骤 3: 计算饱和度 (Saturation)

**公式**：
```python
if delta == 0:
    S = 0  # 灰色，无饱和度
else:
    S = delta / (1 - |2*L - 1|)
```

**含义**：
- 分母 `1 - |2*L - 1|` 是一个调节因子
  - 当 L = 0 或 L = 1 时，分母接近 0（极暗或极亮）
  - 当 L = 0.5 时，分母 = 1（中等亮度，饱和度最明显）
- S = 0: 完全不饱和（灰色）
- S = 1: 完全饱和（纯色）

**例子**：
```
S = 0.5 / (1 - |2*0.55 - 1|)
  = 0.5 / (1 - |1.1 - 1|)
  = 0.5 / (1 - 0.1)
  = 0.5 / 0.9
  = 0.556
```

---

### 步骤 4: 计算色相 (Hue)

**公式**（根据最大颜色分量决定）：

```python
if delta == 0:
    H = 0  # 未定义（灰色）
elif max_c == R:
    H = 60 * (((G - B) / delta) % 6)
elif max_c == G:
    H = 60 * (((B - R) / delta) + 2)
elif max_c == B:
    H = 60 * (((R - G) / delta) + 4)

# 确保 H 在 [0, 360) 范围内
if H < 0:
    H = H + 360
```

**含义**：
- 色相表示在色轮上的位置（角度）
- 0° / 360°: 红色
- 60°: 黄色
- 120°: 绿色
- 180°: 青色
- 240°: 蓝色
- 300°: 洋红

**例子**（max_c = R = 0.8）：
```
H = 60 * (((0.5 - 0.3) / 0.5) % 6)
  = 60 * ((0.2 / 0.5) % 6)
  = 60 * (0.4 % 6)
  = 60 * 0.4
  = 24°
```

这是一个橙红色（介于红色0°和黄色60°之间）

---

## 完整示例

### 输入：RGB = (204, 128, 77) / 255 = (0.8, 0.5, 0.3)

```
步骤 1:
  max_c = 0.8 (R)
  min_c = 0.3 (B)
  delta = 0.5

步骤 2 (Lightness):
  L = (0.8 + 0.3) / 2 = 0.55

步骤 3 (Saturation):
  S = 0.5 / (1 - |2*0.55 - 1|)
    = 0.5 / 0.9
    = 0.556

步骤 4 (Hue):
  因为 max = R:
  H = 60 * ((0.5 - 0.3) / 0.5)
    = 60 * 0.4
    = 24°
```

### 结果：
- **Hue** = 24° (橙红色)
- **Saturation** = 55.6% (中等饱和)
- **Lightness** = 55% (中等亮度)

---

## 肤色的典型 HSL 范围

在 ChromaCloud 项目中，我们关注的肤色范围：

```
Hue (色相):        约 0-50°
                   (红色到橙色范围，这是人类肤色的主要色相)

Saturation (饱和度): 约 20-60%
                      (不会太灰也不会太艳)

Lightness (亮度):   约 30-70%
                     (从较深肤色到较浅肤色)
```

---

## 代码实现（NumPy 向量化）

```python
def rgb_to_hsl(rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    高性能 RGB 到 HSL 转换
    
    Args:
        rgb: RGB 数组 (..., 3)，范围 [0, 1]
    
    Returns:
        (H, S, L) 其中 H 在 [0, 360]，S 和 L 在 [0, 1]
    """
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    
    # 1. 计算最大、最小、差值
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c
    
    # 2. 计算亮度
    l = (max_c + min_c) / 2.0
    
    # 3. 计算饱和度
    s = np.zeros_like(l)
    mask = delta != 0  # 只处理非灰色像素
    s[mask] = delta[mask] / (1 - np.abs(2 * l[mask] - 1) + 1e-10)
    
    # 4. 计算色相
    h = np.zeros_like(l)
    
    # 根据哪个通道是最大值来计算
    r_max = (max_c == r) & mask
    g_max = (max_c == g) & mask
    b_max = (max_c == b) & mask
    
    h[r_max] = 60 * (((g[r_max] - b[r_max]) / delta[r_max]) % 6)
    h[g_max] = 60 * (((b[g_max] - r[g_max]) / delta[g_max]) + 2)
    h[b_max] = 60 * (((r[b_max] - g[b_max]) / delta[b_max]) + 4)
    
    # 确保色相为正值
    h[h < 0] += 360
    
    return h, s, l
```

---

## 为什么使用 HSL？

### 1. **更符合人类感知**
   - RGB 是设备相关的
   - HSL 更接近人类描述颜色的方式
   - "这是一个浅橙色" = H≈30°, S≈40%, L≈70%

### 2. **肤色分析的优势**
   - **Hue** 区分不同种族的肤色基调
   - **Saturation** 反映皮肤健康度（血液循环）
   - **Lightness** 表示肤色深浅

### 3. **统计分析更有意义**
   - 肤色的 Hue 均值：表示主要色调
   - Hue 标准差：表示肤色均匀度
   - Lightness 分布：可以分析明暗区域

---

## 实际应用示例

在 ChromaCloud 中：

1. **面部检测** → 提取面部区域像素
2. **RGB → HSL 转换** → 每个像素转换为 HSL
3. **统计分析**：
   ```
   平均 Hue: 18.5°     (偏红橙色)
   平均 Saturation: 45% (中等饱和)
   平均 Lightness: 52%  (中等亮度)
   ```
4. **亮度分布**：
   ```
   Low (<33%):  15.3%   (阴影区域)
   Mid (33-67%): 68.4%  (主要肤色)
   High (>67%): 16.3%   (高光区域)
   ```

---

## 参考资料

- [Wikipedia: HSL and HSV](https://en.wikipedia.org/wiki/HSL_and_HSV)
- [RGB to HSL Conversion Formula](https://www.rapidtables.com/convert/color/rgb-to-hsl.html)
- OpenCV: cv2.cvtColor(img, cv2.COLOR_RGB2HLS)

---

**ChromaCloud 项目**
专注于面部肤色分析的专业工具
