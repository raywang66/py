"""
3D HSL 参考线可视化演示
显示所有参考线的角度和位置
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle, FancyArrowPatch
import matplotlib.patches as mpatches

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def draw_reference_lines():
    """绘制俯视图，显示所有参考线的角度"""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # ========== 左图: 俯视图 (Top View) ==========
    ax1.set_xlim(-1.3, 1.3)
    ax1.set_ylim(-1.3, 1.3)
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_title('3D HSL 圆柱楔形 - 俯视图 (Top View)', fontsize=16, weight='bold', pad=20)
    ax1.set_xlabel('X 轴 (East)', fontsize=12)
    ax1.set_ylabel('Z 轴 (North)', fontsize=12)

    # 外圆 (最大饱和度)
    circle_outer = Circle((0, 0), 1.0, fill=False, color='gray', linewidth=2, linestyle='-', alpha=0.6)
    ax1.add_patch(circle_outer)

    # 中圆 (50% 饱和度)
    circle_mid = Circle((0, 0), 0.5, fill=False, color='gray', linewidth=1, linestyle='--', alpha=0.4)
    ax1.add_patch(circle_mid)

    # 肤色楔形区域 (15° - 25°)
    wedge = Wedge((0, 0), 1.0, 15, 25, facecolor='peachpuff', edgecolor='orange',
                  linewidth=2, alpha=0.3, label='肤色范围 (15°-25°)')
    ax1.add_patch(wedge)

    # 参考线
    lines_data = [
        (0,   'red',    '🔴 0° (红色参考)', 2.5),
        (15,  'gold',   '🟡 15° (楔形起点)', 2.0),
        (20,  'silver', '⚪ 20° (楔形中心)', 2.0),
        (25,  'gold',   '🟡 25° (楔形终点)', 2.0),
    ]

    for angle_deg, color, label, lw in lines_data:
        angle_rad = np.radians(angle_deg)
        x_end = 1.1 * np.cos(angle_rad)
        z_end = 1.1 * np.sin(angle_rad)

        # 绘制从中心到外圈的线
        ax1.plot([0, x_end], [0, z_end], color=color, linewidth=lw,
                label=label, alpha=0.8)

        # 在线的末端添加角度标注
        text_x = 1.2 * np.cos(angle_rad)
        text_z = 1.2 * np.sin(angle_rad)
        ax1.text(text_x, text_z, f'{angle_deg}°', fontsize=12, weight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7))

    # 添加坐标轴箭头
    ax1.arrow(0, 0, 1.15, 0, head_width=0.05, head_length=0.08,
             fc='black', ec='black', linewidth=1.5)
    ax1.text(1.25, 0, 'X', fontsize=14, weight='bold')

    ax1.arrow(0, 0, 0, 1.15, head_width=0.05, head_length=0.08,
             fc='black', ec='black', linewidth=1.5)
    ax1.text(0, 1.25, 'Z', fontsize=14, weight='bold')

    # 添加中心点
    ax1.plot(0, 0, 'ko', markersize=8, label='中心 (S=0)')

    # 图例
    ax1.legend(loc='upper right', fontsize=10, framealpha=0.9)

    # ========== 右图: 色相色轮 ==========
    ax2.set_xlim(-1.3, 1.3)
    ax2.set_ylim(-1.3, 1.3)
    ax2.set_aspect('equal')
    ax2.set_title('色相色轮 (Hue Wheel) - 360°', fontsize=16, weight='bold', pad=20)
    ax2.axis('off')

    # 绘制完整的色轮
    n_segments = 360
    for i in range(n_segments):
        angle_start = i
        angle_end = i + 1

        # HSL to RGB 转换 (简化版)
        h = i / 360.0
        # 简单的 HSL to RGB (L=0.5, S=1.0)
        if h < 1/6:
            r, g, b = 1, 6*h, 0
        elif h < 2/6:
            r, g, b = 2-6*h, 1, 0
        elif h < 3/6:
            r, g, b = 0, 1, 6*h-2
        elif h < 4/6:
            r, g, b = 0, 4-6*h, 1
        elif h < 5/6:
            r, g, b = 6*h-4, 0, 1
        else:
            r, g, b = 1, 0, 6-6*h

        wedge = Wedge((0, 0), 1.0, angle_start, angle_end,
                     facecolor=(r, g, b), edgecolor='none')
        ax2.add_patch(wedge)

    # 标注主要颜色
    color_markers = [
        (0,   '红色\n(Red)', 'red'),
        (60,  '黄色\n(Yellow)', 'yellow'),
        (120, '绿色\n(Green)', 'lime'),
        (180, '青色\n(Cyan)', 'cyan'),
        (240, '蓝色\n(Blue)', 'blue'),
        (300, '洋红\n(Magenta)', 'magenta'),
    ]

    for angle_deg, name, color in color_markers:
        angle_rad = np.radians(angle_deg)
        x = 1.15 * np.cos(angle_rad)
        z = 1.15 * np.sin(angle_rad)
        ax2.text(x, z, f'{angle_deg}°\n{name}', fontsize=10, weight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                         edgecolor=color, linewidth=2, alpha=0.9))

    # 高亮肤色区域 (15-25°)
    wedge_skin = Wedge((0, 0), 1.0, 15, 25, facecolor='none',
                      edgecolor='orange', linewidth=4, alpha=0.8)
    ax2.add_patch(wedge_skin)

    # 标注肤色区域
    skin_angle = np.radians(20)
    skin_x = 0.7 * np.cos(skin_angle)
    skin_z = 0.7 * np.sin(skin_angle)
    ax2.text(skin_x, skin_z, '肤色\n15-25°', fontsize=12, weight='bold',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='peachpuff',
                     edgecolor='orange', linewidth=2))

    # 添加中心白色圆
    circle_center = Circle((0, 0), 0.15, facecolor='white', edgecolor='black', linewidth=2)
    ax2.add_patch(circle_center)

    plt.tight_layout()
    plt.savefig('3D_HSL_Reference_Lines_Visualization.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    print("✅ 图表已保存: 3D_HSL_Reference_Lines_Visualization.png")
    plt.show()


def print_summary():
    """打印参考线总结"""
    print("\n" + "="*70)
    print("3D HSL 圆柱楔形 - 参考线总结")
    print("="*70)

    print("\n【圆形参考线】(灰色)")
    print("  • 底部圆 (Y=0.0): 深灰色 - 标记暗色区域边界")
    print("  • 中部圆 (Y=0.5): 浅灰色 - 标记中等亮度")
    print("  • 顶部圆 (Y=1.0): 深灰色 - 标记亮色区域边界")

    print("\n【径向参考线】(色相标记)")
    print("  🔴 红色线 - 0° (Y=0.5)")
    print("     ↳ 色相原点参考 (纯红色方向)")
    print("     ↳ 颜色: [1.0, 0.2, 0.2] (亮红色)")

    print("\n  🟡 黄色线 #1 - 15° (Y=0.0)")
    print("     ↳ 肤色楔形起点 (最偏红的肤色)")
    print("     ↳ 颜色: [0.8, 0.8, 0.2] (黄色)")

    print("\n  ⚪ 白色线 - 20° (Y=0.5)")
    print("     ↳ 肤色楔形中心 (典型肤色)")
    print("     ↳ 颜色: [0.6, 0.6, 0.6] (浅灰色)")

    print("\n  🟡 黄色线 #2 - 25° (Y=1.0)")
    print("     ↳ 肤色楔形终点 (最偏橙的肤色)")
    print("     ↳ 颜色: [0.8, 0.8, 0.2] (黄色)")

    print("\n【肤色楔形区域】")
    print("  • 色相范围: 15° - 25° (10° 扇形)")
    print("  • 饱和度: 0 - 1 (从中心到外圈)")
    print("  • 亮度: 0 - 1 (从底到顶)")

    print("\n【角度对照表】")
    print("  0° ──→ 红色 (Red)")
    print("  15° ─→ 红橙色 (肤色下限)")
    print("  20° ─→ 橙红色 (典型肤色) ⭐")
    print("  25° ─→ 橙色 (肤色上限)")
    print("  60° ─→ 黄色 (Yellow)")
    print("  120° ─→ 绿色 (Green)")
    print("  180° ─→ 青色 (Cyan)")
    print("  240° ─→ 蓝色 (Blue)")
    print("  300° ─→ 洋红 (Magenta)")

    print("\n" + "="*70)
    print("ChromaCloud 3D HSL 可视化系统")
    print("="*70 + "\n")


if __name__ == "__main__":
    print_summary()
    print("\n正在生成可视化图表...")
    draw_reference_lines()
