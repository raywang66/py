"""
ChromaCloud (CC) - Skin Segmentation & Color Extraction Module
Author: Senior Software Architect
Date: January 2026

MediaPipe-based AI skin segmentation pipeline that feeds into Taichi rendering.
Uses MediaPipe Face Mesh for modern, easy-to-install face detection.
EXCLUDES non-skin regions: eyebrows, eyes, lips, facial hair.
SUPPORTS Sony RAW files (.arw) and other RAW formats via rawpy.
"""

import logging
from typing import Optional, Tuple, Union
from pathlib import Path

import numpy as np
import cv2
from PIL import Image

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("WARNING: MediaPipe not installed. Install with: pip install mediapipe")

try:
    import rawpy
    RAWPY_AVAILABLE = True
except ImportError:
    RAWPY_AVAILABLE = False
    print("WARNING: rawpy not installed. RAW file support disabled. Install with: pip install rawpy")

from cc_config import (
    CC_SKIN_CONFIG,
    CC_HSL_CONFIG,
    CC_LOG_LEVEL
)

# Configure logger
logging.basicConfig(level=CC_LOG_LEVEL)
logger = logging.getLogger("CC_SkinProcessor")


class CC_MediaPipeFaceDetector:
    """
    Modern face detection using Google MediaPipe.

    Advantages over BiSeNet:
    - No manual model download required
    - Actively maintained (2024+)
    - Fast CPU inference
    - Precise face landmarks (468 points)
    """

    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe not installed. Run: pip install mediapipe")

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

        # Face mesh landmark indices for different regions
        # These are standard MediaPipe Face Mesh indices
        self.FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                          397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                          172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158,
                         159, 160, 161, 246]

        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388,
                          387, 386, 385, 384, 398]

        self.LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324,
                     318, 402, 317, 14, 87, 178, 88, 95, 78, 191, 80, 81, 82, 13,
                     312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]

        self.LEFT_EYEBROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
        self.RIGHT_EYEBROW = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]

        logger.info("MediaPipe Face Mesh initialized")

    def detect_face_mask(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        Detect face and create skin mask using MediaPipe.

        Args:
            image_rgb: RGB image (H, W, 3) with values [0, 255]

        Returns:
            Binary mask (H, W) where 1 = skin, 0 = non-skin
        """
        h, w = image_rgb.shape[:2]

        # Process with MediaPipe
        results = self.face_mesh.process(image_rgb)

        if not results.multi_face_landmarks:
            logger.warning("No face detected in image")
            return np.zeros((h, w), dtype=np.uint8)

        # Get face landmarks
        face_landmarks = results.multi_face_landmarks[0]

        # Create mask
        mask = np.zeros((h, w), dtype=np.uint8)

        # Convert landmarks to pixel coordinates
        def landmarks_to_points(indices):
            points = []
            for idx in indices:
                landmark = face_landmarks.landmark[idx]
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                points.append([x, y])
            return np.array(points, dtype=np.int32)

        # Fill face oval (entire face region)
        face_points = landmarks_to_points(self.FACE_OVAL)
        cv2.fillPoly(mask, [face_points], 1)

        # Exclude eyes
        left_eye_points = landmarks_to_points(self.LEFT_EYE)
        right_eye_points = landmarks_to_points(self.RIGHT_EYE)
        cv2.fillPoly(mask, [left_eye_points], 0)
        cv2.fillPoly(mask, [right_eye_points], 0)

        # Exclude lips
        lips_points = landmarks_to_points(self.LIPS)
        cv2.fillPoly(mask, [lips_points], 0)

        # Exclude eyebrows
        left_brow_points = landmarks_to_points(self.LEFT_EYEBROW)
        right_brow_points = landmarks_to_points(self.RIGHT_EYEBROW)
        cv2.fillPoly(mask, [left_brow_points], 0)
        cv2.fillPoly(mask, [right_brow_points], 0)

        logger.info(f"Face mask created: {mask.sum() / mask.size * 100:.1f}% coverage")

        return mask


class CC_SkinProcessor:
    """
    High-performance skin segmentation and HSL extraction pipeline.

    Uses MediaPipe Face Mesh (modern, easy-to-install alternative to BiSeNet).

    Pipeline:
        1. Load image (JPEG/PNG/RAW)
        2. Detect face with MediaPipe
        3. Generate skin mask (exclude eyes, brows, lips)
        4. Convert masked pixels to HSL
        5. Filter by hue range [15°, 25°]
        6. Output Nx3 point cloud (H, S, L)

    Supported formats:
        - Standard: JPEG, PNG, TIFF, BMP
        - RAW: Sony .arw, Nikon .nef, Canon .cr2/.cr3, Adobe .dng, etc.

    Usage:
        >>> processor = CC_SkinProcessor()
        >>> point_cloud = processor.process_image("portrait.jpg")
        >>> print(point_cloud.shape)  # (N, 3) - H, S, L coordinates
    """

    def __init__(
        self,
        use_mediapipe: bool = True,
        config: Optional[object] = None
    ):
        """
        Initialize the skin processor.

        Args:
            use_mediapipe: Use MediaPipe for face detection (recommended)
            config: Override default configuration
        """
        self.config = config or CC_SKIN_CONFIG
        self.hsl_config = CC_HSL_CONFIG

        # Initialize face detector
        if use_mediapipe and MEDIAPIPE_AVAILABLE:
            self.face_detector = CC_MediaPipeFaceDetector()
            logger.info("Using MediaPipe Face Mesh for detection")
        else:
            logger.warning("MediaPipe not available, using color-based heuristic")
            self.face_detector = None

    def process_image(
        self,
        image_path: Union[str, Path, np.ndarray, Image.Image],
        return_mask: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Process an image and extract skin tone point cloud.

        Args:
            image_path: Path to image or numpy array or PIL Image
            return_mask: If True, also return the binary skin mask

        Returns:
            point_cloud: Nx3 array of (H, S, L) coordinates
            mask: (Optional) HxW binary mask if return_mask=True
        """
        # Load image
        image_rgb = self._load_image(image_path)

        # Generate skin mask
        if self.face_detector:
            skin_mask = self.face_detector.detect_face_mask(image_rgb)
        else:
            # Fallback: color-based heuristic
            skin_mask = self._heuristic_skin_mask(image_rgb)

        # Apply morphological operations
        if self.config.apply_morphology:
            skin_mask = self._apply_morphology(skin_mask)

        # Convert RGB to HSL for masked pixels
        point_cloud = self._extract_hsl_points(image_rgb, skin_mask)

        # Note: We do NOT filter by hue range here!
        # We keep ALL pixels to preserve true skin color information
        # Users need to see if there are pixels <15° (too red) or >25° (too yellow)

        # Downsample if needed
        point_cloud = self._downsample_points(point_cloud)

        logger.info(f"Extracted {len(point_cloud)} skin tone points")

        if return_mask:
            return point_cloud, skin_mask
        return point_cloud

    def _load_image(
        self,
        image_input: Union[str, Path, np.ndarray, Image.Image]
    ) -> np.ndarray:
        """Load image from various sources and return RGB numpy array [0, 255]

        Supports:
        - Standard formats: JPEG, PNG, etc. (via PIL)
        - RAW formats: .arw, .nef, .cr2, .dng, etc. (via rawpy)
        - NumPy arrays
        - PIL Image objects
        """
        if isinstance(image_input, (str, Path)):
            image_path = Path(image_input)

            # Check if it's a RAW file
            raw_extensions = {'.arw', '.nef', '.cr2', '.cr3', '.dng', '.raf', '.rw2', '.orf'}
            if image_path.suffix.lower() in raw_extensions:
                # Handle RAW file
                if not RAWPY_AVAILABLE:
                    raise ImportError(
                        f"Cannot load RAW file {image_path.name}: rawpy not installed.\n"
                        f"Install with: pip install rawpy"
                    )

                logger.info(f"Loading RAW file: {image_path.name}")
                with rawpy.imread(str(image_path)) as raw:
                    # Process RAW with specific parameters for color accuracy
                    # Same settings as skin_color_matcher.py
                    rgb = raw.postprocess(
                        gamma=(1, 1),          # Linear output first
                        no_auto_bright=True,   # Disable auto brightness
                        use_camera_wb=True,    # Use camera white balance
                        output_bps=16          # 16-bit output for precision
                    )

                # Convert from 16-bit to 8-bit RGB
                # Normalize to [0, 255] range
                rgb_8bit = (rgb / 256).astype(np.uint8)
                logger.info(f"RAW file processed: {rgb_8bit.shape}, dtype={rgb_8bit.dtype}")
                return rgb_8bit
            else:
                # Handle standard image formats (JPEG, PNG, etc.)
                image = Image.open(image_input).convert("RGB")
                return np.array(image)

        elif isinstance(image_input, Image.Image):
            return np.array(image_input.convert("RGB"))
        elif isinstance(image_input, np.ndarray):
            if image_input.ndim == 2:  # Grayscale
                return cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
            # Ensure uint8 range
            if image_input.dtype == np.float32 or image_input.dtype == np.float64:
                if image_input.max() <= 1.0:
                    return (image_input * 255).astype(np.uint8)
            return image_input.astype(np.uint8)
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

    def _heuristic_skin_mask(self, image_rgb: np.ndarray) -> np.ndarray:
        """Fallback: color-based skin detection (less accurate)"""
        logger.warning("Using heuristic skin detection (install MediaPipe for better results)")

        # Convert to HSV
        hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)

        # Skin color range in HSV
        lower_skin = np.array([0, 20, 50])
        upper_skin = np.array([30, 255, 255])

        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        return (mask > 0).astype(np.uint8)

    def _apply_morphology(self, mask: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up mask"""
        kernel_size = self.config.morph_kernel_size
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

        # Remove small noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Fill small holes
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def _extract_hsl_points(
        self,
        image_rgb: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """Extract HSL coordinates from masked pixels"""
        # Get masked pixel RGB values
        masked_pixels = image_rgb[mask == 1]  # Shape: (N, 3)

        if len(masked_pixels) == 0:
            logger.error("No skin pixels detected!")
            return np.array([]).reshape(0, 3)

        # Convert RGB to HSL
        hsl_points = self._rgb_to_hsl(masked_pixels)

        return hsl_points

    @staticmethod
    def _rgb_to_hsl(rgb_array: np.ndarray) -> np.ndarray:
        """
        Convert RGB to HSL color space.

        Args:
            rgb_array: (N, 3) array with RGB values in [0, 255]

        Returns:
            hsl_array: (N, 3) array with HSL values:
                       H in [0, 360] degrees
                       S in [0, 1]
                       L in [0, 1]
        """
        rgb_normalized = rgb_array.astype(np.float32) / 255.0
        r, g, b = rgb_normalized[:, 0], rgb_normalized[:, 1], rgb_normalized[:, 2]

        max_c = np.max(rgb_normalized, axis=1)
        min_c = np.min(rgb_normalized, axis=1)
        delta = max_c - min_c

        # Lightness
        lightness = (max_c + min_c) / 2.0

        # Saturation
        saturation = np.zeros_like(lightness)
        mask_nonzero = delta != 0
        saturation[mask_nonzero] = delta[mask_nonzero] / (
            1 - np.abs(2 * lightness[mask_nonzero] - 1)
        )

        # Hue
        hue = np.zeros_like(lightness)

        r_max = (max_c == r) & mask_nonzero
        g_max = (max_c == g) & mask_nonzero
        b_max = (max_c == b) & mask_nonzero

        hue[r_max] = ((g[r_max] - b[r_max]) / delta[r_max]) % 6
        hue[g_max] = ((b[g_max] - r[g_max]) / delta[g_max]) + 2
        hue[b_max] = ((r[b_max] - g[b_max]) / delta[b_max]) + 4

        hue = hue * 60.0  # Convert to degrees [0, 360]

        return np.stack([hue, saturation, lightness], axis=1)

    def _filter_by_hue(self, hsl_points: np.ndarray) -> np.ndarray:
        """Filter points by hue range for skin tones"""
        if len(hsl_points) == 0:
            return hsl_points

        hue = hsl_points[:, 0]
        saturation = hsl_points[:, 1]
        lightness = hsl_points[:, 2]

        # Apply filters
        hue_mask = (hue >= self.hsl_config.hue_min) & (hue <= self.hsl_config.hue_max)
        sat_mask = (saturation >= self.hsl_config.saturation_min / 100.0) & \
                   (saturation <= self.hsl_config.saturation_max / 100.0)
        light_mask = (lightness >= self.hsl_config.lightness_min / 100.0) & \
                     (lightness <= self.hsl_config.lightness_max / 100.0)

        final_mask = hue_mask & sat_mask & light_mask
        filtered_points = hsl_points[final_mask]

        logger.info(f"Hue filter: {len(hsl_points)} → {len(filtered_points)} points")

        return filtered_points

    def _downsample_points(self, points: np.ndarray) -> np.ndarray:
        """Downsample point cloud if too large"""
        if len(points) <= self.hsl_config.max_points:
            return points

        method = self.hsl_config.downsample_method
        max_points = self.hsl_config.max_points

        if method == "random":
            indices = np.random.choice(len(points), max_points, replace=False)
            return points[indices]
        elif method == "uniform":
            step = len(points) // max_points
            return points[::step][:max_points]
        else:
            return points

    def process_dual_images(
        self,
        image_a: Union[str, Path, np.ndarray],
        image_b: Union[str, Path, np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Process two images in parallel for dual-view comparison.

        Args:
            image_a: First image (e.g., "White" reference)
            image_b: Second image (e.g., "Golden" reference)

        Returns:
            (point_cloud_a, point_cloud_b): Two Nx3 arrays
        """
        logger.info("Processing dual images for comparison...")

        point_cloud_a = self.process_image(image_a)
        point_cloud_b = self.process_image(image_b)

        logger.info(f"Dual processing complete: {len(point_cloud_a)} vs {len(point_cloud_b)} points")

        return point_cloud_a, point_cloud_b


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("ChromaCloud - CC_SkinProcessor Demo (MediaPipe)")
    print("=" * 60)

    if not MEDIAPIPE_AVAILABLE:
        print("\nERROR: MediaPipe not installed!")
        print("Install with: pip install mediapipe")
        exit(1)

    # Initialize processor
    processor = CC_SkinProcessor()

    # Test with existing photos
    from pathlib import Path
    photos_dir = Path(__file__).parent / "Photos"

    if photos_dir.exists():
        test_images = list(photos_dir.glob("*.JPG")) + list(photos_dir.glob("*.jpg")) + list(photos_dir.glob("*.arw"))

        if test_images:
            test_image = test_images[0]
            print(f"\nProcessing: {test_image.name}")

            point_cloud, mask = processor.process_image(test_image, return_mask=True)

            print(f"✓ Extracted {len(point_cloud)} points")
            if len(point_cloud) > 0:
                print(f"✓ HSL range: H=[{point_cloud[:, 0].min():.1f}°, {point_cloud[:, 0].max():.1f}°]")
            print(f"✓ Mask coverage: {mask.sum() / mask.size * 100:.1f}%")
        else:
            print("No test images found in Photos/ directory")
    else:
        print("Photos/ directory not found")

