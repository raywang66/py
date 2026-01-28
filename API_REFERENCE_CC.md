# ChromaCloud (CC) - API Reference

## Table of Contents
1. [CC_SkinProcessor](#cc_skinprocessor)
2. [CC_Renderer3D](#cc_renderer3d)
3. [CC_MainApp](#cc_mainapp)
4. [Configuration](#configuration)

---

## CC_SkinProcessor

High-performance skin segmentation and HSL extraction pipeline.

### Class: `CC_SkinProcessor`

```python
from CC_SkinProcessor import CC_SkinProcessor

processor = CC_SkinProcessor(
    model_path=None,        # Path to face parsing model
    use_gpu=True,          # Enable CUDA/Metal
    config=None            # Override default config
)
```

#### Methods

##### `process_image(image_path, return_mask=False)`

Process an image and extract skin tone point cloud.

**Parameters:**
- `image_path` (str | Path | np.ndarray | PIL.Image): Input image
- `return_mask` (bool): Return binary mask along with point cloud

**Returns:**
- `np.ndarray`: Nx3 array of (H, S, L) coordinates
  - H: Hue in [0, 360] degrees
  - S: Saturation in [0, 1]
  - L: Lightness in [0, 1]
- `np.ndarray` (optional): HxW binary mask if `return_mask=True`

**Example:**
```python
point_cloud = processor.process_image("portrait.jpg")
print(f"Extracted {len(point_cloud)} points")

# With mask
cloud, mask = processor.process_image("portrait.jpg", return_mask=True)
```

##### `process_dual_images(image_a, image_b)`

Process two images for dual-view comparison.

**Parameters:**
- `image_a` (str | Path | np.ndarray): First image
- `image_b` (str | Path | np.ndarray): Second image

**Returns:**
- `Tuple[np.ndarray, np.ndarray]`: Two Nx3 point clouds

**Example:**
```python
cloud_a, cloud_b = processor.process_dual_images(
    "white_reference.jpg",
    "golden_reference.jpg"
)
```

---

## CC_Renderer3D

Taichi-based real-time 3D point cloud renderer.

### Class: `CC_Renderer3D`

```python
from CC_Renderer3D import CC_Renderer3D

renderer = CC_Renderer3D(
    width=800,           # Viewport width
    height=600,          # Viewport height
    backend='vulkan',    # 'metal', 'vulkan', 'dx12', 'cuda', 'cpu'
    config=None
)
```

#### Methods

##### `set_point_cloud(hsl_points, color=None)`

Upload point cloud to GPU.

**Parameters:**
- `hsl_points` (np.ndarray): Nx3 array of (H, S, L) coordinates
- `color` (Tuple[float, float, float], optional): RGB color in [0, 1]

**Example:**
```python
renderer.set_point_cloud(point_cloud, color=(1.0, 0.4, 0.4))
```

##### `set_dual_point_clouds(hsl_points_a, hsl_points_b, color_a=None, color_b=None)`

Upload two point clouds for overlay visualization.

**Parameters:**
- `hsl_points_a` (np.ndarray): First point cloud
- `hsl_points_b` (np.ndarray): Second point cloud
- `color_a` (Tuple[float, float, float], optional): Color for cloud A
- `color_b` (Tuple[float, float, float], optional): Color for cloud B

**Example:**
```python
renderer.set_dual_point_clouds(
    cloud_a, cloud_b,
    color_a=(1.0, 0.42, 0.42),  # Red
    color_b=(0.31, 0.80, 0.77)   # Cyan
)
```

##### `render()`

Render the current scene.

**Returns:**
- `np.ndarray`: RGBA image (H, W, 4) with values in [0, 1]

**Example:**
```python
rgba_image = renderer.render()
```

##### `get_image_uint8()`

Get rendered image as uint8 array for display.

**Returns:**
- `np.ndarray`: RGBA image (H, W, 4) with values in [0, 255]

##### `save_screenshot(filepath)`

Save current render to file.

**Parameters:**
- `filepath` (str): Output path (PNG format)

**Example:**
```python
renderer.save_screenshot("output/skin_analysis.png")
```

##### `update_camera(azimuth=None, elevation=None, distance=None)`

Update camera position.

**Parameters:**
- `azimuth` (float, optional): Rotation around Z-axis (degrees)
- `elevation` (float, optional): Rotation above XY plane (degrees)
- `distance` (float, optional): Distance from origin

---

## CC_MainApp

Main application entry point with PySide6 UI.

### Class: `CC_MainApp`

```python
from CC_MainApp import CC_MainApp

app = CC_MainApp()
exit_code = app.run()
```

#### Methods

##### `run()`

Run the application event loop.

**Returns:**
- `int`: Exit code

**Example:**
```python
import sys
from CC_MainApp import CC_MainApp

def main():
    app = CC_MainApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
```

---

## Configuration

### Global Configuration Objects

All configuration is centralized in `cc_config.py`:

#### `CC_SkinSegmentationConfig`

```python
from cc_config import CC_SKIN_CONFIG

# Access properties
print(CC_SKIN_CONFIG.model_name)        # 'bisenet'
print(CC_SKIN_CONFIG.input_size)        # (512, 512)
print(CC_SKIN_CONFIG.skin_classes)      # [1, 2, 3, 10, 11, 12, 13]
print(CC_SKIN_CONFIG.exclude_classes)   # [4, 5, 6, 7, 8, 9, 17]

# Modify at runtime
CC_SKIN_CONFIG.use_fp16 = False
CC_SKIN_CONFIG.apply_morphology = True
```

#### `CC_HSLConfig`

```python
from cc_config import CC_HSL_CONFIG

# Hue range for skin tones
CC_HSL_CONFIG.hue_min = 10.0   # degrees
CC_HSL_CONFIG.hue_max = 30.0   # degrees

# Saturation/Lightness filters
CC_HSL_CONFIG.saturation_min = 10.0  # %
CC_HSL_CONFIG.lightness_min = 20.0   # %

# Point cloud downsampling
CC_HSL_CONFIG.max_points = 50000
CC_HSL_CONFIG.downsample_method = "uniform"  # or "random"
```

#### `CC_Renderer3DConfig`

```python
from cc_config import CC_RENDERER_CONFIG

# Viewport settings
CC_RENDERER_CONFIG.viewport_width = 1200
CC_RENDERER_CONFIG.viewport_height = 800

# Rendering quality
CC_RENDERER_CONFIG.point_size = 2.5
CC_RENDERER_CONFIG.point_alpha = 0.8

# Dual-view colors
CC_RENDERER_CONFIG.dual_color_a = (1.0, 0.5, 0.0)  # Orange
CC_RENDERER_CONFIG.dual_color_b = (0.0, 0.5, 1.0)  # Blue
```

#### `CC_UIConfig`

```python
from cc_config import CC_UI_CONFIG

# Window dimensions
CC_UI_CONFIG.window_width = 1600
CC_UI_CONFIG.window_height = 1000

# Theme
CC_UI_CONFIG.theme = "dark"  # or "light"
CC_UI_CONFIG.accent_color = "#FF6B6B"

# Photo grid
CC_UI_CONFIG.thumbnail_size = 250
CC_UI_CONFIG.grid_spacing = 15
```

---

## Helper Functions

### `CC_load_pretrained_model(model_name='bisenet')`

Download or locate pre-trained face parsing model.

**Returns:**
- `str`: Path to model weights

**Example:**
```python
from CC_SkinProcessor import CC_load_pretrained_model

model_path = CC_load_pretrained_model("bisenet")
processor = CC_SkinProcessor(model_path=model_path)
```

### `CC_create_test_point_cloud(num_points=10000)`

Generate test HSL point cloud for development.

**Returns:**
- `np.ndarray`: Nx3 array with synthetic skin tone data

**Example:**
```python
from CC_Renderer3D import CC_create_test_point_cloud

test_data = CC_create_test_point_cloud(5000)
renderer.set_point_cloud(test_data)
```

---

## Complete Example

```python
from CC_SkinProcessor import CC_SkinProcessor
from CC_Renderer3D import CC_Renderer3D
import numpy as np

# Initialize modules
processor = CC_SkinProcessor(use_gpu=True)
renderer = CC_Renderer3D(width=1024, height=768)

# Process image
point_cloud = processor.process_image("portrait.jpg")
print(f"Extracted {len(point_cloud)} skin tone points")

# Analyze statistics
hue_mean = point_cloud[:, 0].mean()
sat_mean = point_cloud[:, 1].mean()
light_mean = point_cloud[:, 2].mean()

print(f"Average Hue: {hue_mean:.1f}°")
print(f"Average Saturation: {sat_mean*100:.1f}%")
print(f"Average Lightness: {light_mean*100:.1f}%")

# Render 3D visualization
renderer.set_point_cloud(point_cloud)
rgba_image = renderer.get_image_uint8()

# Save output
renderer.save_screenshot("output/skin_analysis.png")
```

---

## Error Handling

All CC modules use Python logging. Enable debug mode:

```python
import logging
from cc_config import CC_LOG_LEVEL

logging.basicConfig(level=logging.DEBUG)
```

Common exceptions:
- `FileNotFoundError`: Model or image file not found
- `RuntimeError`: GPU initialization failed
- `ValueError`: Invalid configuration parameters

---

**ChromaCloud API v1.0.0** | © 2026

