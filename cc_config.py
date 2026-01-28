"""
ChromaCloud (CC) - Global Configuration
Author: Senior Software Architect
Date: January 2026

Central configuration for all CC modules.
"""

import platform
from pathlib import Path
from dataclasses import dataclass
from typing import Literal

# ============================================================================
# PROJECT METADATA
# ============================================================================
CC_PROJECT_NAME = "ChromaCloud"
CC_VERSION = "1.0.0"
CC_AUTHOR = "CV/Image Processing Team"

# ============================================================================
# PATHS
# ============================================================================
CC_ROOT_DIR = Path(__file__).parent
CC_MODELS_DIR = CC_ROOT_DIR / "models"
CC_CACHE_DIR = CC_ROOT_DIR / "cache"
CC_DATABASE_PATH = CC_ROOT_DIR / "chromacloud.db"

# Create directories if they don't exist
CC_MODELS_DIR.mkdir(exist_ok=True)
CC_CACHE_DIR.mkdir(exist_ok=True)

# ============================================================================
# GPU CONFIGURATION
# ============================================================================
CC_USE_GPU = True  # Auto-detect CUDA/Metal
CC_GPU_MEMORY_LIMIT_GB = 4  # For RTX 3050 Ti

# Taichi backend selection (auto-detected)
CC_PLATFORM = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'

if CC_PLATFORM == "Darwin":
    CC_TAICHI_BACKEND = "metal"
elif CC_PLATFORM == "Windows":
    CC_TAICHI_BACKEND = "vulkan"  # Fallback: dx12, cuda
else:
    CC_TAICHI_BACKEND = "vulkan"

# ============================================================================
# SKIN SEGMENTATION PARAMETERS
# ============================================================================
@dataclass
class CC_SkinSegmentationConfig:
    """Configuration for MediaPipe-based skin segmentation"""

    # MediaPipe parameters
    use_mediapipe: bool = True
    min_detection_confidence: float = 0.5

    # Post-processing
    apply_morphology: bool = True  # Remove noise with morphological ops
    morph_kernel_size: int = 5
    min_mask_area_ratio: float = 0.01  # Minimum mask area (% of image)

# ============================================================================
# HSL COLOR SPACE CONFIGURATION
# ============================================================================
@dataclass
class CC_HSLConfig:
    """Configuration for HSL 3D visualization"""

    # Hue range for skin tones (in degrees)
    hue_min: float = 15.0
    hue_max: float = 25.0

    # Saturation filter (optional, 0-100%)
    saturation_min: float = 10.0
    saturation_max: float = 100.0

    # Lightness filter (optional, 0-100%)
    lightness_min: float = 20.0  # Exclude very dark shadows
    lightness_max: float = 90.0   # Exclude highlights

    # Point cloud downsampling
    max_points: int = 50000  # Limit for smooth 60 FPS rendering
    downsample_method: Literal["random", "uniform", "none"] = "uniform"

# ============================================================================
# 3D RENDERING CONFIGURATION
# ============================================================================
@dataclass
class CC_Renderer3DConfig:
    """Configuration for Taichi-based 3D rendering"""

    # Viewport resolution
    viewport_width: int = 800
    viewport_height: int = 600

    # Camera settings
    camera_fov: float = 45.0  # Field of view (degrees)
    camera_near: float = 0.1
    camera_far: float = 100.0
    camera_distance: float = 3.0  # Distance from origin

    # Point cloud rendering
    point_size: float = 2.0  # Point size in pixels
    point_alpha: float = 0.7  # Transparency

    # Dual-view colors (RGB normalized)
    dual_color_a: tuple[float, float, float] = (1.0, 0.42, 0.42)  # #FF6B6B - Red
    dual_color_b: tuple[float, float, float] = (0.31, 0.80, 0.77)  # #4ECDC4 - Cyan

    # Background
    background_color: tuple[float, float, float] = (0.12, 0.12, 0.15)  # Dark gray

    # Performance
    target_fps: int = 60
    enable_vsync: bool = True

# ============================================================================
# UI CONFIGURATION
# ============================================================================
@dataclass
class CC_UIConfig:
    """Configuration for PySide6 UI"""

    # Window settings
    window_title: str = "ChromaCloud - Skin Tone Analysis"
    window_width: int = 1400
    window_height: int = 900
    window_min_width: int = 1000
    window_min_height: int = 600

    # macOS effects
    use_translucency: bool = True  # Mica/Acrylic effects
    blur_radius: int = 30

    # Sidebar
    sidebar_width: int = 220
    sidebar_collapsed_width: int = 60

    # Photo grid
    thumbnail_size: int = 200
    grid_spacing: int = 10
    grid_columns: int = -1  # Auto-calculate based on width

    # Theme
    theme: Literal["dark", "light"] = "dark"
    accent_color: str = "#4ECDC4"  # Teal accent

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
@dataclass
class CC_DatabaseConfig:
    """Configuration for SQLite database"""

    db_path: str = str(CC_DATABASE_PATH)
    enable_wal_mode: bool = True  # Write-Ahead Logging for performance
    cache_size_kb: int = 10000  # 10 MB cache

    # Connection pool
    max_connections: int = 5
    timeout_seconds: int = 30

# ============================================================================
# INSTANTIATE GLOBAL CONFIGS
# ============================================================================
CC_SKIN_CONFIG = CC_SkinSegmentationConfig()
CC_HSL_CONFIG = CC_HSLConfig()
CC_RENDERER_CONFIG = CC_Renderer3DConfig()
CC_UI_CONFIG = CC_UIConfig()
CC_DB_CONFIG = CC_DatabaseConfig()

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
CC_LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
CC_LOG_FILE = CC_ROOT_DIR / "chromacloud.log"
CC_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
