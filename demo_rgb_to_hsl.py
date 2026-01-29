"""
RGB to HSL Conversion Demo
演示如何将 RGB 转换为 HSL
"""

import numpy as np


def rgb_to_hsl_step_by_step(r, g, b):
    """
    逐步演示 RGB 到 HSL 的转换过程

    Args:
        r, g, b: RGB 值，范围 [0, 1]
    """
    print(f"\n{'='*60}")
    print(f"输入 RGB: R={r:.3f}, G={g:.3f}, B={b:.3f}")
    print(f"{'='*60}\n")

    # 步骤 1: 计算最大值、最小值、差值
    print("步骤 1: 计算最大值、最小值、差值")
    print("-" * 40)
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c

    print(f"  max_c = max({r:.3f}, {g:.3f}, {b:.3f}) = {max_c:.3f}")
    print(f"  min_c = min({r:.3f}, {g:.3f}, {b:.3f}) = {min_c:.3f}")
    print(f"  delta = max_c - min_c = {delta:.3f}")

    # 步骤 2: 计算亮度 (Lightness)
    print("\n步骤 2: 计算亮度 (Lightness)")
    print("-" * 40)
    L = (max_c + min_c) / 2.0
    print(f"  L = (max_c + min_c) / 2")
    print(f"    = ({max_c:.3f} + {min_c:.3f}) / 2")
    print(f"    = {L:.3f}")
    print(f"  → 亮度 = {L*100:.1f}%")

    # 步骤 3: 计算饱和度 (Saturation)
    print("\n步骤 3: 计算饱和度 (Saturation)")
    print("-" * 40)
    if delta == 0:
        S = 0
        print(f"  delta = 0，所以 S = 0 (灰色)")
    else:
        denominator = 1 - abs(2 * L - 1)
        S = delta / (denominator + 1e-10)
        print(f"  S = delta / (1 - |2*L - 1|)")
        print(f"    = {delta:.3f} / (1 - |2*{L:.3f} - 1|)")
        print(f"    = {delta:.3f} / (1 - |{2*L:.3f} - 1|)")
        print(f"    = {delta:.3f} / (1 - {abs(2*L - 1):.3f})")
        print(f"    = {delta:.3f} / {denominator:.3f}")
        print(f"    = {S:.3f}")
    print(f"  → 饱和度 = {S*100:.1f}%")

    # 步骤 4: 计算色相 (Hue)
    print("\n步骤 4: 计算色相 (Hue)")
    print("-" * 40)
    if delta == 0:
        H = 0
        print(f"  delta = 0，所以 H = 0 (未定义)")
    else:
        if max_c == r:
            print(f"  最大值是 R，使用红色公式：")
            H = 60 * (((g - b) / delta) % 6)
            print(f"  H = 60 * (((G - B) / delta) % 6)")
            print(f"    = 60 * ((({g:.3f} - {b:.3f}) / {delta:.3f}) % 6)")
            print(f"    = 60 * (({(g-b):.3f} / {delta:.3f}) % 6)")
            print(f"    = 60 * ({(g-b)/delta:.3f} % 6)")
            print(f"    = 60 * {((g-b)/delta) % 6:.3f}")
            print(f"    = {H:.1f}°")
        elif max_c == g:
            print(f"  最大值是 G，使用绿色公式：")
            H = 60 * (((b - r) / delta) + 2)
            print(f"  H = 60 * (((B - R) / delta) + 2)")
            print(f"    = 60 * ((({b:.3f} - {r:.3f}) / {delta:.3f}) + 2)")
            print(f"    = 60 * (({(b-r):.3f} / {delta:.3f}) + 2)")
            print(f"    = 60 * ({(b-r)/delta:.3f} + 2)")
            print(f"    = 60 * {((b-r)/delta) + 2:.3f}")
            print(f"    = {H:.1f}°")
        else:  # max_c == b
            print(f"  最大值是 B，使用蓝色公式：")
            H = 60 * (((r - g) / delta) + 4)
            print(f"  H = 60 * (((R - G) / delta) + 4)")
            print(f"    = 60 * ((({r:.3f} - {g:.3f}) / {delta:.3f}) + 4)")
            print(f"    = 60 * (({(r-g):.3f} / {delta:.3f}) + 4)")
            print(f"    = 60 * ({(r-g)/delta:.3f} + 4)")
            print(f"    = 60 * {((r-g)/delta) + 4:.3f}")
            print(f"    = {H:.1f}°")

        if H < 0:
            H += 360
            print(f"  H < 0，所以 H = H + 360 = {H:.1f}°")

    # 解释色相
    color_name = get_color_name(H)
    print(f"  → 色相 = {H:.1f}° ({color_name})")

    # 最终结果
    print(f"\n{'='*60}")
    print(f"最终结果:")
    print(f"  H (色相)   = {H:.1f}° ({color_name})")
    print(f"  S (饱和度) = {S:.3f} ({S*100:.1f}%)")
    print(f"  L (亮度)   = {L:.3f} ({L*100:.1f}%)")
    print(f"{'='*60}\n")

    return H, S, L


def get_color_name(hue):
    """根据色相角度返回颜色名称"""
    if hue < 30:
        return "红色"
    elif hue < 60:
        return "橙色"
    elif hue < 90:
        return "黄橙色"
    elif hue < 150:
        return "绿色"
    elif hue < 210:
        return "青色"
    elif hue < 270:
        return "蓝色"
    elif hue < 330:
        return "紫色"
    else:
        return "红色"


def rgb_255_to_hsl(r255, g255, b255):
    """
    从 0-255 范围的 RGB 转换为 HSL

    Args:
        r255, g255, b255: RGB 值，范围 [0, 255]
    """
    print(f"\n输入 RGB (0-255): R={r255}, G={g255}, B={b255}")
    print(f"归一化: R={r255/255:.3f}, G={g255/255:.3f}, B={b255/255:.3f}")

    return rgb_to_hsl_step_by_step(r255/255, g255/255, b255/255)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RGB 到 HSL 转换演示")
    print("="*60)

    # 示例 1: 典型肤色 (浅肤色)
    print("\n" + "🎨 示例 1: 典型浅肤色")
    rgb_255_to_hsl(255, 220, 177)  # 浅肤色

    # 示例 2: 典型肤色 (中等肤色)
    print("\n" + "🎨 示例 2: 典型中等肤色")
    rgb_255_to_hsl(204, 128, 77)   # 中等肤色

    # 示例 3: 典型肤色 (深肤色)
    print("\n" + "🎨 示例 3: 典型深肤色")
    rgb_255_to_hsl(141, 85, 36)    # 深肤色

    # 示例 4: 纯红色
    print("\n" + "🎨 示例 4: 纯红色")
    rgb_255_to_hsl(255, 0, 0)

    # 示例 5: 灰色 (无饱和度)
    print("\n" + "🎨 示例 5: 中灰色 (无饱和度)")
    rgb_255_to_hsl(128, 128, 128)

    print("\n" + "="*60)
    print("演示完成！")
    print("="*60)
