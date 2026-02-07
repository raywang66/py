"""
ChromaCloud (CC) - 3D Point Cloud Renderer
Author: Senior Software Architect
Date: January 2026

Real-time 3D HSL cylindrical wedge visualization using Taichi Lang.
Renders skin tone point clouds in HSL color space with GPU acceleration.

Features:
- 3D cylindrical coordinate system (Hue as angle, Saturation as radius, Lightness as height)
- Interactive camera controls
- Dual-view mode for comparing two point clouds
- Cross-platform GPU support (CUDA/Vulkan/Metal)
"""

import numpy as np
import taichi as ti
from pathlib import Path
from typing import Optional, Tuple

from cc_config import CC_RENDERER_CONFIG, CC_PLATFORM, CC_TAICHI_BACKEND

# Initialize Taichi with appropriate backend (only once)
_taichi_initialized = False
if not _taichi_initialized:
    try:
        if CC_PLATFORM == "Darwin":  # macOS
            ti.init(arch=ti.metal)
        elif CC_PLATFORM == "Windows":
            try:
                ti.init(arch=ti.vulkan)
            except:
                ti.init(arch=ti.cpu)
        else:
            ti.init(arch=ti.cpu)
        _taichi_initialized = True
    except Exception as e:
        print(f"Taichi initialization warning: {e}")
        _taichi_initialized = True  # Prevent repeated initialization attempts


@ti.data_oriented
class CC_Renderer3D:
    """
    High-performance 3D point cloud renderer for HSL color space visualization.

    Coordinate System:
    - X-axis: Horizontal (camera right)
    - Y-axis: Vertical (up)
    - Z-axis: Depth (forward)

    HSL Mapping to Cylindrical Coordinates:
    - Hue (H): Angular position around cylinder (0-360°)
    - Saturation (S): Radial distance from center (0-1)
    - Lightness (L): Height along Y-axis (0-1)
    """

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height

        # Create frame buffer
        self.pixels = ti.Vector.field(3, dtype=ti.f32, shape=(width, height))

        # Point cloud data
        self.max_points = CC_RENDERER_CONFIG.max_points if hasattr(CC_RENDERER_CONFIG, 'max_points') else 50000
        self.points = ti.Vector.field(3, dtype=ti.f32, shape=self.max_points)
        self.colors = ti.Vector.field(3, dtype=ti.f32, shape=self.max_points)
        self.num_points = ti.field(ti.i32, shape=())

        # Dual-view mode
        self.points_b = ti.Vector.field(3, dtype=ti.f32, shape=self.max_points)
        self.colors_b = ti.Vector.field(3, dtype=ti.f32, shape=self.max_points)
        self.num_points_b = ti.field(ti.i32, shape=())
        self.dual_mode = ti.field(ti.i32, shape=())

        # Camera parameters - better angle to show 3D cylinder
        self.camera_pos = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.camera_lookat = ti.Vector.field(3, dtype=ti.f32, shape=())
        self.camera_up = ti.Vector.field(3, dtype=ti.f32, shape=())

        # Initialize camera at optimal angle to see vertical Y-axis (Lightness)
        # Position camera at nearly horizontal level to make Y-axis appear vertical on screen
        self.camera_angle_h = 45.0   # Horizontal angle in degrees (around Y-axis)
        self.camera_angle_v = 0.0    # Vertical angle in degrees (0 = eye level, makes Y-axis vertical on screen)
        self.camera_distance = 3.5
        self._update_camera_position()

        # Rendering parameters
        self.point_size = CC_RENDERER_CONFIG.point_size if hasattr(CC_RENDERER_CONFIG, 'point_size') else 2.0
        self.bg_color = CC_RENDERER_CONFIG.background_color if hasattr(CC_RENDERER_CONFIG, 'background_color') else (0.12, 0.12, 0.15)

        # Axis visualization data
        self.max_axis_points = 2000
        self.axis_points = ti.Vector.field(3, dtype=ti.f32, shape=self.max_axis_points)
        self.axis_colors = ti.Vector.field(3, dtype=ti.f32, shape=self.max_axis_points)
        self.num_axis_points = ti.field(ti.i32, shape=())

        # Generate axis visualization
        self._generate_axes()

    def _update_camera_position(self):
        """Update camera position based on angles"""
        import math

        # Convert angles to radians
        angle_h_rad = math.radians(self.camera_angle_h)
        angle_v_rad = math.radians(self.camera_angle_v)

        # Use spherical coordinates but ensure Y-axis alignment
        # Place camera on XZ plane (horizontal) to make Y-axis appear vertical
        radius_xz = self.camera_distance * math.cos(angle_v_rad)

        x = radius_xz * math.cos(angle_h_rad)
        z = radius_xz * math.sin(angle_h_rad)
        y = 0.5 + self.camera_distance * math.sin(angle_v_rad)

        self.camera_pos[None] = [x, y, z]
        self.camera_lookat[None] = [0.0, 0.5, 0.0]  # Look at cylinder center
        self.camera_up[None] = [0.0, 1.0, 0.0]      # Y is always up

    def _generate_axes(self):
        """Generate cylindrical coordinate system visualization"""
        axis_pts = []
        axis_cols = []

        # Vertical axis (Lightness: 0 to 1)
        for i in range(50):
            t = i / 49.0
            axis_pts.append([0.0, t, 0.0])
            axis_cols.append([0.5, 0.5, 0.5])  # Gray

        # Horizontal circle at bottom (Saturation reference at L=0)
        for i in range(60):
            angle = (i / 60.0) * 2 * np.pi
            radius = 1.0
            axis_pts.append([radius * np.cos(angle), 0.0, radius * np.sin(angle)])
            axis_cols.append([0.3, 0.3, 0.3])  # Dark gray

        # Horizontal circle at top (Saturation reference at L=1)
        for i in range(60):
            angle = (i / 60.0) * 2 * np.pi
            radius = 1.0
            axis_pts.append([radius * np.cos(angle), 1.0, radius * np.sin(angle)])
            axis_cols.append([0.3, 0.3, 0.3])  # Dark gray

        # Radial lines for hue reference (15° to 25° wedge)
        # Line at 15° (start of wedge) - Yellow marker
        for i in range(20):
            t = i / 19.0
            angle = np.radians(15)
            radius = t * 1.0
            axis_pts.append([radius * np.cos(angle), 0.0, radius * np.sin(angle)])
            axis_cols.append([0.8, 0.8, 0.2])  # Yellow

        # Line at 20° (middle) - White marker
        for i in range(20):
            t = i / 19.0
            angle = np.radians(20)
            radius = t * 1.0
            axis_pts.append([radius * np.cos(angle), 0.5, radius * np.sin(angle)])
            axis_cols.append([0.6, 0.6, 0.6])  # Light gray

        # Line at 25° (end of wedge) - Yellow marker
        for i in range(20):
            t = i / 19.0
            angle = np.radians(25)
            radius = t * 1.0
            axis_pts.append([radius * np.cos(angle), 1.0, radius * np.sin(angle)])
            axis_cols.append([0.8, 0.8, 0.2])  # Yellow

        # Red reference line at 0° (H=0 reference)
        for i in range(20):
            t = i / 19.0
            angle = 0.0
            radius = t * 1.0
            axis_pts.append([radius * np.cos(angle), 0.5, radius * np.sin(angle)])
            axis_cols.append([1.0, 0.2, 0.2])  # Bright red

        # Convert to numpy and upload to GPU
        axis_pts = np.array(axis_pts, dtype=np.float32)
        axis_cols = np.array(axis_cols, dtype=np.float32)

        n = min(len(axis_pts), self.max_axis_points)
        self.num_axis_points[None] = n
        self.axis_points.from_numpy(axis_pts[:n])
        self.axis_colors.from_numpy(axis_cols[:n])

    def set_point_cloud(self, hsl_points: np.ndarray, color_mode: str = 'hsl'):
        """
        Set point cloud data from HSL coordinates.

        Args:
            hsl_points: Nx3 array with (Hue[0-360], Saturation[0-1], Lightness[0-1])
            color_mode: 'hsl' (use HSL values) or 'uniform' (single color)
        """
        import logging
        logger = logging.getLogger("CC_Renderer3D")

        total_points = len(hsl_points)
        n = min(total_points, self.max_points)
        self.num_points[None] = n
        self.dual_mode[None] = 0

        if total_points > self.max_points:
            logger.warning(f"Point cloud has {total_points:,} points, but renderer is limited to {self.max_points:,} points. "
                         f"{total_points - self.max_points:,} points will not be displayed.")
        else:
            logger.info(f"Rendering {n:,} points")

        # Convert HSL to 3D cylindrical coordinates
        positions = np.zeros((n, 3), dtype=np.float32)
        colors = np.zeros((n, 3), dtype=np.float32)

        for i in range(n):
            h, s, l = hsl_points[i]

            # Cylindrical coordinates: (angle, radius, height)
            angle = np.radians(h)  # Hue as angle
            radius = s             # Saturation as radius
            height = l             # Lightness as height

            # Convert to Cartesian (X, Y, Z)
            x = radius * np.cos(angle)
            z = radius * np.sin(angle)
            y = height

            positions[i] = [x, y, z]

            # Color: convert HSL back to RGB for display
            if color_mode == 'hsl':
                colors[i] = self._hsl_to_rgb(h / 360.0, s, l)
            else:
                colors[i] = [0.98, 0.42, 0.42]  # Red tint

        # Upload to GPU
        self.points.from_numpy(positions)
        self.colors.from_numpy(colors)

    def set_dual_point_clouds(self, hsl_points_a: np.ndarray, hsl_points_b: np.ndarray):
        """
        Set two point clouds for comparison mode.

        Args:
            hsl_points_a: First point cloud (displayed in color A)
            hsl_points_b: Second point cloud (displayed in color B)
        """
        self.dual_mode[None] = 1

        # Set first cloud
        n_a = min(len(hsl_points_a), self.max_points)
        self.num_points[None] = n_a

        positions_a = np.zeros((n_a, 3), dtype=np.float32)
        colors_a = np.zeros((n_a, 3), dtype=np.float32)

        dual_color_a = CC_RENDERER_CONFIG.dual_color_a if hasattr(CC_RENDERER_CONFIG, 'dual_color_a') else (1.0, 0.42, 0.42)

        for i in range(n_a):
            h, s, l = hsl_points_a[i]
            angle = np.radians(h)
            radius = s
            height = l

            positions_a[i] = [radius * np.cos(angle), height, radius * np.sin(angle)]
            colors_a[i] = dual_color_a

        self.points.from_numpy(positions_a)
        self.colors.from_numpy(colors_a)

        # Set second cloud
        n_b = min(len(hsl_points_b), self.max_points)
        self.num_points_b[None] = n_b

        positions_b = np.zeros((n_b, 3), dtype=np.float32)
        colors_b = np.zeros((n_b, 3), dtype=np.float32)

        dual_color_b = CC_RENDERER_CONFIG.dual_color_b if hasattr(CC_RENDERER_CONFIG, 'dual_color_b') else (0.31, 0.80, 0.77)

        for i in range(n_b):
            h, s, l = hsl_points_b[i]
            angle = np.radians(h)
            radius = s
            height = l

            positions_b[i] = [radius * np.cos(angle), height, radius * np.sin(angle)]
            colors_b[i] = dual_color_b

        self.points_b.from_numpy(positions_b)
        self.colors_b.from_numpy(colors_b)

    @staticmethod
    def _hsl_to_rgb(h: float, s: float, l: float) -> np.ndarray:
        """Convert HSL to RGB (all values 0-1)"""
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h * 6) % 2 - 1))
        m = l - c / 2

        if h < 1/6:
            r, g, b = c, x, 0
        elif h < 2/6:
            r, g, b = x, c, 0
        elif h < 3/6:
            r, g, b = 0, c, x
        elif h < 4/6:
            r, g, b = 0, x, c
        elif h < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return np.array([r + m, g + m, b + m], dtype=np.float32)

    @ti.kernel
    def render(self):
        """Render the point cloud to the frame buffer"""
        # Clear background
        for i, j in self.pixels:
            self.pixels[i, j] = ti.Vector([self.bg_color[0], self.bg_color[1], self.bg_color[2]])

        # Setup camera
        cam_pos = self.camera_pos[None]
        cam_lookat = self.camera_lookat[None]
        cam_up = self.camera_up[None]

        # Camera coordinate system
        forward = (cam_lookat - cam_pos).normalized()
        right = forward.cross(cam_up).normalized()
        up = right.cross(forward)

        # Projection parameters
        fov = 45.0
        aspect = float(self.width) / float(self.height)
        near = 0.1
        far = 100.0

        # Render axis visualization FIRST (so points draw on top)
        for idx in range(self.num_axis_points[None]):
            pos = self.axis_points[idx]
            color = self.axis_colors[idx]

            # World to camera space
            rel_pos = pos - cam_pos
            cam_x = rel_pos.dot(right)
            cam_y = rel_pos.dot(up)
            cam_z = rel_pos.dot(forward)

            if cam_z > near:
                # Perspective projection
                screen_x = (cam_x / cam_z) / ti.tan(ti.math.radians(fov / 2)) / aspect
                screen_y = (cam_y / cam_z) / ti.tan(ti.math.radians(fov / 2))

                # Convert to pixel coordinates
                px = int((screen_x + 1.0) * 0.5 * self.width)
                py = int((1.0 - screen_y) * 0.5 * self.height)

                # Draw axis point (smaller)
                if 0 <= px < self.width and 0 <= py < self.height:
                    self.pixels[px, py] = color
                    # Make axes slightly thicker
                    if px + 1 < self.width:
                        self.pixels[px + 1, py] = color
                    if py + 1 < self.height:
                        self.pixels[px, py + 1] = color

        # Render data point cloud
        for idx in range(self.num_points[None]):
            pos = self.points[idx]
            color = self.colors[idx]

            # World to camera space
            rel_pos = pos - cam_pos
            cam_x = rel_pos.dot(right)
            cam_y = rel_pos.dot(up)
            cam_z = rel_pos.dot(forward)

            if cam_z > near:
                # Perspective projection
                screen_x = (cam_x / cam_z) / ti.tan(ti.math.radians(fov / 2)) / aspect
                screen_y = (cam_y / cam_z) / ti.tan(ti.math.radians(fov / 2))

                # Convert to pixel coordinates
                px = int((screen_x + 1.0) * 0.5 * self.width)
                py = int((1.0 - screen_y) * 0.5 * self.height)

                # Draw point with larger size for visibility
                if 0 <= px < self.width and 0 <= py < self.height:
                    # Point splatting with size
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            nx, ny = px + dx, py + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                self.pixels[nx, ny] = color

        # Render second point cloud (if dual mode)
        if self.dual_mode[None] == 1:
            for idx in range(self.num_points_b[None]):
                pos = self.points_b[idx]
                color = self.colors_b[idx]

                # World to camera space
                rel_pos = pos - cam_pos
                cam_x = rel_pos.dot(right)
                cam_y = rel_pos.dot(up)
                cam_z = rel_pos.dot(forward)

                if cam_z > near:
                    # Perspective projection
                    screen_x = (cam_x / cam_z) / ti.tan(ti.math.radians(fov / 2)) / aspect
                    screen_y = (cam_y / cam_z) / ti.tan(ti.math.radians(fov / 2))

                    # Convert to pixel coordinates
                    px = int((screen_x + 1.0) * 0.5 * self.width)
                    py = int((1.0 - screen_y) * 0.5 * self.height)

                    # Draw point
                    if 0 <= px < self.width and 0 <= py < self.height:
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                nx, ny = px + dx, py + dy
                                if 0 <= nx < self.width and 0 <= ny < self.height:
                                    self.pixels[nx, ny] = color

    def get_image(self) -> np.ndarray:
        """Get rendered image as numpy array (H, W, 3) with values [0, 255]"""
        img = self.pixels.to_numpy()
        img = (img * 255).clip(0, 255).astype(np.uint8)
        return img

    def save_screenshot(self, filepath: str):
        """Save rendered image to file"""
        from PIL import Image
        img = self.get_image()
        Image.fromarray(img).save(filepath)
        print(f"Screenshot saved: {filepath}")

    def rotate_camera(self, delta_h: float, delta_v: float):
        """Rotate camera by delta angles"""
        self.camera_angle_h += delta_h
        self.camera_angle_v += delta_v

        # Clamp vertical angle to avoid flipping
        self.camera_angle_v = max(-80, min(80, self.camera_angle_v))

        self._update_camera_position()

    def zoom_camera(self, delta: float):
        """Zoom camera in/out"""
        self.camera_distance += delta
        self.camera_distance = max(1.5, min(8.0, self.camera_distance))
        self._update_camera_position()

    def set_camera_angles(self, angle_h: float, angle_v: float):
        """Set camera to specific angles (in degrees)"""
        self.camera_angle_h = angle_h
        self.camera_angle_v = max(-89, min(89, angle_v))  # Clamp to avoid gimbal lock
        self._update_camera_position()


def CC_create_test_point_cloud(num_points: int = 1000) -> np.ndarray:
    """
    Create a test point cloud for demonstration.

    Returns:
        Nx3 array with HSL coordinates
    """
    np.random.seed(42)

    # Generate points in skin tone range
    hue = np.random.uniform(15, 25, num_points)  # Skin tone hue range
    saturation = np.random.uniform(0.2, 0.8, num_points)
    lightness = np.random.uniform(0.3, 0.9, num_points)

    return np.stack([hue, saturation, lightness], axis=1).astype(np.float32)


if __name__ == "__main__":
    print("=" * 60)
    print("ChromaCloud - CC_Renderer3D Test")
    print("=" * 60)

    # Create renderer
    renderer = CC_Renderer3D(800, 600)
    print(f"✓ Renderer initialized ({renderer.width}x{renderer.height})")

    # Create test data
    points = CC_create_test_point_cloud(5000)
    print(f"✓ Generated {len(points)} test points")

    # Set point cloud
    renderer.set_point_cloud(points)
    print(f"✓ Point cloud uploaded to GPU")

    # Render
    renderer.render()
    img = renderer.get_image()
    print(f"✓ Rendered image: {img.shape}")

    # Save
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    renderer.save_screenshot(str(output_dir / "test_render.png"))

    print("\n✓ Test complete!")
