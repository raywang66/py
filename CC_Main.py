"""
ChromaCloud (CC) - Main GUI Application
Author: Senior Software Architect
Date: January 2026

Modern desktop UI for skin tone analysis with Albums management.
Features:
- Album-based photo organization
- Batch processing with HSL distribution analysis
- Complete statistics with Lightness/Hue/Saturation comparison charts
- Database-backed photo management
- MediaPipe face detection
- 3D HSL visualization
"""

import sys
import logging
import platform
from pathlib import Path

# =============================================================================
# Platform-specific data directory setup
# =============================================================================
def get_data_directory():
    """Get platform-specific data directory for ChromaCloud files"""
    os_type = platform.system()

    if os_type == "Darwin":  # macOS
        # Use ~/CC for data files when running on macOS (SMB share friendly)
        data_dir = Path.home() / "CC"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    else:
        # Windows/Linux: use script directory
        return Path(__file__).parent

# Get data directory
DATA_DIR = get_data_directory()
LOG_FILE = DATA_DIR / "chromacloud.log"
DB_FILE = DATA_DIR / "chromacloud.db"

# =============================================================================
# CRITICAL: Configure logging FIRST, before any other imports!
# Other modules (CC_SkinProcessor, CC_Database, etc.) create loggers during import.
# If basicConfig() is not called first, Python creates a default buffer handler
# that can cause NUL bytes and corruption in the log file.
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(relativeCreated)d ms [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler(str(LOG_FILE), mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Ensure console output is UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Now safe to import other modules - logging is configured
import time
from typing import Optional, List
import pickle

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QScrollArea, QGridLayout,
    QSplitter, QGroupBox, QProgressBar, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QInputDialog, QMenu, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QPalette, QColor, QAction, QFont

import numpy as np
from PIL import Image
import cv2

# Matplotlib for distribution charts
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO

from cc_config import CC_PROJECT_NAME, CC_VERSION
from CC_SkinProcessor import CC_SkinProcessor, MEDIAPIPE_AVAILABLE, RAWPY_AVAILABLE
from CC_Database import CC_Database


logger = logging.getLogger("CC_MainApp")
logger.info(f"ChromaCloud data directory: {DATA_DIR}")
logger.info(f"Database: {DB_FILE}")
logger.info(f"Log file: {LOG_FILE}")


# =============================================================================
# Helper Functions
# =============================================================================

def should_skip_file(file_path: Path) -> bool:
    """
    Check if file should be skipped (AppleDouble and macOS metadata files).

    Filters out:
    - .DS_Store (macOS folder metadata)
    - ._* files (AppleDouble resource fork files)
    - .Spotlight-V100 (macOS Spotlight index)
    - .Trashes (macOS trash)
    - .fseventsd (macOS file system events)
    - .TemporaryItems (macOS temporary files)
    - Thumbs.db (Windows thumbnail cache)
    - desktop.ini (Windows folder settings)
    """
    filename = file_path.name

    # Skip macOS metadata files
    if filename == '.DS_Store':
        return True

    # Skip AppleDouble resource fork files (._filename)
    if filename.startswith('._'):
        return True

    # Skip macOS system directories
    if filename in {'.Spotlight-V100', '.Trashes', '.fseventsd', '.TemporaryItems',
                    '.VolumeIcon.icns', '.DocumentRevisions-V100', '.PKInstallSandboxManager'}:
        return True

    # Skip Windows metadata files
    if filename in {'Thumbs.db', 'desktop.ini', 'Desktop.ini'}:
        return True

    return False


# =============================================================================
# Thread Classes
# =============================================================================

class FolderScanWorker(QThread):
    """Background thread for scanning folder structure (performance optimization)"""
    scan_completed = Signal(int, dict)  # album_id, structure
    progress_updated = Signal(str)      # status message

    def __init__(self, album_id: int, folder_path: str):
        super().__init__()
        self.album_id = album_id
        self.folder_path = Path(folder_path)
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.nef',
                                '.cr2', '.cr3', '.dng',
                                '.JPG', '.JPEG', '.PNG', '.ARW', '.NEF',
                                '.CR2', '.CR3', '.DNG'}

    def run(self):
        """Scan folder structure in background"""
        try:
            logger.info(f"Background scan started for album {self.album_id}: {self.folder_path}")
            structure = self._scan_folder_structure(self.folder_path)
            self.scan_completed.emit(self.album_id, structure)
            logger.info(f"Background scan completed for album {self.album_id}")
        except Exception as e:
            logger.error(f"Background scan error: {e}")

    def _scan_folder_structure(self, dir_path: Path, parent_path: Optional[str] = None) -> dict:
        """Recursively scan folder structure"""
        structure = {
            'path': str(dir_path),
            'parent_path': parent_path,
            'direct_photos': 0,
            'total_photos': 0,
            'subdirs': []
        }

        if not dir_path.exists() or not dir_path.is_dir():
            return structure

        try:
            # Count direct photos (skip AppleDouble and metadata files)
            for item in dir_path.iterdir():
                if item.is_file() and item.suffix in self.image_extensions:
                    # Skip AppleDouble and metadata files
                    if should_skip_file(item):
                        continue
                    structure['direct_photos'] += 1

            structure['total_photos'] = structure['direct_photos']

            # Recursively scan subdirectories
            subdirs = sorted([d for d in dir_path.iterdir() if d.is_dir()],
                           key=lambda x: x.name.lower())

            for subdir in subdirs:
                # Skip hidden, system directories, and macOS metadata
                if subdir.name.startswith('.') or subdir.name.startswith('__'):
                    continue
                if should_skip_file(subdir):
                    continue

                sub_structure = self._scan_folder_structure(subdir, str(dir_path))
                if sub_structure['total_photos'] > 0:
                    structure['subdirs'].append(sub_structure)
                    structure['total_photos'] += sub_structure['total_photos']

        except (PermissionError, OSError) as e:
            logger.warning(f"Error scanning {dir_path}: {e}")

        return structure


class CC_ProcessingThread(QThread):
    """Background thread for single image processing"""
    progress = Signal(int)
    finished = Signal(object, object, object)  # point_cloud, mask, rgb_image
    error = Signal(str)

    def __init__(self, processor: CC_SkinProcessor, image_path: Path):
        super().__init__()
        self.processor = processor
        self.image_path = image_path

    def run(self):
        try:
            logger.info(f"Processing: {self.image_path}")
            self.progress.emit(10)
            image_rgb = self.processor._load_image(self.image_path)
            self.progress.emit(30)
            point_cloud, mask = self.processor.process_image(image_rgb, return_mask=True)
            self.progress.emit(100)
            self.finished.emit(point_cloud, mask, image_rgb)
        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            self.error.emit(str(e))


class CC_BatchProcessingThread(QThread):
    """Background thread for batch processing multiple photos"""
    progress = Signal(int, str)  # percentage, current_file
    finished = Signal(list)  # results list
    error = Signal(str)

    def __init__(self, processor: CC_SkinProcessor, photo_paths: List[Path]):
        super().__init__()
        self.processor = processor
        self.photo_paths = photo_paths

    def run(self):
        try:
            results = []
            total = len(self.photo_paths)

            for i, photo_path in enumerate(self.photo_paths):
                self.progress.emit(int((i / total) * 100), photo_path.name)

                try:
                    image_rgb = self.processor._load_image(photo_path)
                    point_cloud, mask = self.processor.process_image(image_rgb, return_mask=True)

                    # Calculate statistics
                    if len(point_cloud) > 0:
                        # Calculate lightness distribution (3 ranges)
                        lightness = point_cloud[:, 2]
                        low_light = (lightness < 0.33).sum() / len(lightness) * 100
                        mid_light = ((lightness >= 0.33) & (lightness < 0.67)).sum() / len(lightness) * 100
                        high_light = (lightness >= 0.67).sum() / len(lightness) * 100

                        # Calculate hue distribution (6 ranges)
                        hue = point_cloud[:, 0]
                        hue_very_red = (((hue >= 0) & (hue < 10)) | (hue >= 350)).sum() / len(hue) * 100
                        hue_red_orange = ((hue >= 10) & (hue < 20)).sum() / len(hue) * 100
                        hue_normal = ((hue >= 20) & (hue < 30)).sum() / len(hue) * 100
                        hue_yellow = ((hue >= 30) & (hue < 40)).sum() / len(hue) * 100
                        hue_very_yellow = ((hue >= 40) & (hue < 60)).sum() / len(hue) * 100
                        hue_abnormal = ((hue >= 60) & (hue < 350)).sum() / len(hue) * 100

                        # Calculate saturation distribution (5 ranges, convert 0-1 to 0-100)
                        saturation = point_cloud[:, 1] * 100
                        sat_very_low = (saturation < 15).sum() / len(saturation) * 100
                        sat_low = ((saturation >= 15) & (saturation < 30)).sum() / len(saturation) * 100
                        sat_normal = ((saturation >= 30) & (saturation < 50)).sum() / len(saturation) * 100
                        sat_high = ((saturation >= 50) & (saturation < 70)).sum() / len(saturation) * 100
                        sat_very_high = (saturation >= 70).sum() / len(saturation) * 100

                        result = {
                            'path': photo_path,
                            'success': True,
                            'num_points': len(point_cloud),
                            'mask_coverage': mask.sum() / mask.size,
                            'hue_mean': point_cloud[:, 0].mean(),
                            'hue_std': point_cloud[:, 0].std(),
                            'saturation_mean': point_cloud[:, 1].mean(),
                            'lightness_mean': point_cloud[:, 2].mean(),
                            'lightness_low': low_light,
                            'lightness_mid': mid_light,
                            'lightness_high': high_light,
                            'hue_very_red': hue_very_red,
                            'hue_red_orange': hue_red_orange,
                            'hue_normal': hue_normal,
                            'hue_yellow': hue_yellow,
                            'hue_very_yellow': hue_very_yellow,
                            'hue_abnormal': hue_abnormal,
                            'sat_very_low': sat_very_low,
                            'sat_low': sat_low,
                            'sat_normal': sat_normal,
                            'sat_high': sat_high,
                            'sat_very_high': sat_very_high,
                            'point_cloud': point_cloud
                        }
                    else:
                        result = {'path': photo_path, 'success': False, 'error': 'No face detected'}

                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {photo_path}: {e}")
                    results.append({'path': photo_path, 'success': False, 'error': str(e)})

            self.progress.emit(100, "Complete")
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Batch processing error: {e}", exc_info=True)
            self.error.emit(str(e))


class CC_PhotoThumbnail(QFrame):
    """Photo thumbnail widget with proper aspect ratio - OPTIMIZED with lazy loading and database cache"""

    def __init__(self, image_path: Path, db=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.db = db  # Database for thumbnail cache
        self.setFrameStyle(QFrame.NoFrame)
        self.setLineWidth(0)
        self.setFixedSize(220, 270)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Thumbnail with fixed container but preserving aspect ratio
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(210, 210)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: transparent; border: none;")

        # Show placeholder immediately
        self._show_placeholder()

        # Load thumbnail asynchronously
        self._load_thumbnail_async()

        # Filename
        filename_label = QLabel(image_path.name)
        filename_label.setWordWrap(True)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet("color: #000; font-size: 11px; background-color: transparent;")
        filename_label.setMaximumHeight(40)

        layout.addWidget(self.thumbnail_label)
        layout.addWidget(filename_label)

        self.setStyleSheet("""
            CC_PhotoThumbnail {
                background-color: transparent;
                border: none;
            }
            CC_PhotoThumbnail:hover {
                background-color: transparent;
            }
        """)

    def _show_placeholder(self):
        """Show placeholder while loading"""
        pixmap = QPixmap(210, 210)
        pixmap.fill(QColor(240, 240, 240))

        # Draw loading icon (simple gray square with text)
        from PySide6.QtGui import QPainter, QFont
        painter = QPainter(pixmap)
        painter.setPen(QColor(180, 180, 180))
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Loading...")
        painter.end()

        self.thumbnail_label.setPixmap(pixmap)

    def _load_thumbnail_async(self):
        """Load thumbnail in background using QTimer (non-blocking)"""
        from PySide6.QtCore import QTimer
        # Schedule thumbnail loading with slight delay to not block UI
        QTimer.singleShot(1, self._load_thumbnail)

    def _load_thumbnail(self):
        """Load thumbnail preserving aspect ratio - WITH DATABASE CACHE"""
        thumbnail_start = time.time()
        thumbnail_bytes = None
        cache_hit = False

        try:
            # ⚡️ STEP 1: Try to load from database cache
            if self.db and self.image_path.exists():
                file_mtime = self.image_path.stat().st_mtime
                cache = self.db.get_thumbnail_cache(str(self.image_path))

                if cache and cache['photo_mtime'] == file_mtime:
                    # Cache hit! Load from database (fast!)
                    from io import BytesIO
                    img = Image.open(BytesIO(cache['thumbnail_data']))
                    cache_hit = True
                    logger.debug(f"Cache HIT: {self.image_path.name}")

                    # Update access time for LRU
                    self.db.update_thumbnail_access_time(str(self.image_path))

                    # Convert to QPixmap and display
                    data = img.tobytes('raw', 'RGB')
                    qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)
                    self.thumbnail_label.setPixmap(pixmap)

                    # Track statistics
                    thumbnail_elapsed = time.time() - thumbnail_start
                    if hasattr(CC_PhotoThumbnail, '_cache_hit_count'):
                        CC_PhotoThumbnail._cache_hit_count += 1
                        CC_PhotoThumbnail._cache_hit_time += thumbnail_elapsed
                    else:
                        CC_PhotoThumbnail._cache_hit_count = 1
                        CC_PhotoThumbnail._cache_hit_time = thumbnail_elapsed

                    return  # Done!

            # ⚡️ STEP 2: Cache miss - generate thumbnail
            logger.debug(f"Cache MISS: {self.image_path.name} - generating...")

            # Fast path: try to use embedded thumbnail for JPEG
            if self.image_path.suffix.lower() in {'.jpg', '.jpeg'}:
                img = Image.open(self.image_path)

                # Try to extract embedded thumbnail (much faster)
                try:
                    img.draft('RGB', (210, 210))  # Fast low-quality load
                except:
                    pass

            elif self.image_path.suffix.lower() in {'.arw', '.nef', '.cr2', '.cr3', '.dng'}:
                if RAWPY_AVAILABLE:
                    import rawpy
                    with rawpy.imread(str(self.image_path)) as raw:
                        thumb = raw.extract_thumb()
                        if thumb.format == rawpy.ThumbFormat.JPEG:
                            from io import BytesIO
                            img = Image.open(BytesIO(thumb.data))
                        else:
                            rgb = raw.postprocess(use_camera_wb=True, half_size=True)
                            img = Image.fromarray(rgb)
                else:
                    pixmap = QPixmap(210, 210)
                    pixmap.fill(QColor(245, 245, 245))
                    self.thumbnail_label.setPixmap(pixmap)
                    return
            else:
                img = Image.open(self.image_path)

            # Resize preserving aspect ratio - use LANCZOS for quality
            img.thumbnail((210, 210), Image.Resampling.LANCZOS)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to QPixmap
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.thumbnail_label.setPixmap(pixmap)

            # ⚡️ STEP 3: Save to database cache for next time
            if self.db and self.image_path.exists():
                from io import BytesIO
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                thumbnail_data = buffer.getvalue()

                file_mtime = self.image_path.stat().st_mtime
                self.db.save_thumbnail_cache(
                    str(self.image_path),
                    file_mtime,
                    thumbnail_data,
                    img.width,
                    img.height
                )
                logger.debug(f"Cached: {self.image_path.name} ({len(thumbnail_data)/1024:.1f} KB)")

            # 📊 Calculate thumbnail size (for profiling)
            from io import BytesIO
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            thumbnail_bytes = buffer.getvalue()
            thumbnail_size = len(thumbnail_bytes)

            # 📊 Profile thumbnail loading time and size
            thumbnail_elapsed = time.time() - thumbnail_start

            # Track global statistics (for database storage evaluation)
            if not hasattr(CC_PhotoThumbnail, '_total_thumbnail_time'):
                CC_PhotoThumbnail._total_thumbnail_time = 0
                CC_PhotoThumbnail._total_thumbnail_size = 0
                CC_PhotoThumbnail._thumbnail_count = 0
                CC_PhotoThumbnail._thumbnail_samples = []
                CC_PhotoThumbnail._cache_hit_count = 0
                CC_PhotoThumbnail._cache_hit_time = 0
                CC_PhotoThumbnail._cache_miss_count = 0
                CC_PhotoThumbnail._cache_miss_time = 0

            CC_PhotoThumbnail._total_thumbnail_time += thumbnail_elapsed
            CC_PhotoThumbnail._total_thumbnail_size += thumbnail_size
            CC_PhotoThumbnail._thumbnail_count += 1
            CC_PhotoThumbnail._cache_miss_count += 1
            CC_PhotoThumbnail._cache_miss_time += thumbnail_elapsed

            # Keep some samples for statistics
            if len(CC_PhotoThumbnail._thumbnail_samples) < 10:
                CC_PhotoThumbnail._thumbnail_samples.append({
                    'name': self.image_path.name,
                    'time': thumbnail_elapsed,
                    'size': thumbnail_size
                })

        except Exception as e:
            logger.error(f"Failed to load thumbnail for {self.image_path.name}: {e}")
            pixmap = QPixmap(210, 210)
            pixmap.fill(QColor(245, 245, 245))
            self.thumbnail_label.setPixmap(pixmap)


# =============================================================================
# Main Window
# =============================================================================

class CC_MainWindow(QMainWindow):
    """Main application window - Album-based photo management"""

    def __init__(self):
        super().__init__()

        # Initialize components
        if not MEDIAPIPE_AVAILABLE:
            QMessageBox.critical(self, "Missing Dependency",
                "MediaPipe is not installed!\n\nInstall with: pip install mediapipe")
            sys.exit(1)

        self.processor = CC_SkinProcessor()
        self.db = CC_Database(db_path=DB_FILE)

        # State
        self.current_photo: Optional[Path] = None
        self.current_album_id: Optional[int] = None
        self.point_cloud: Optional[np.ndarray] = None
        self.current_photo_rgb: Optional[np.ndarray] = None
        self.current_mask: Optional[np.ndarray] = None
        self.dark_mode: bool = False  # Light mode by default
        self._scan_workers: List[FolderScanWorker] = []  # Background scan workers

        # ⚠️ TEMPORARY: Disable FolderWatcher to focus on UI rendering performance
        # TODO: Re-enable after UI performance is optimized
        self.ENABLE_FOLDER_WATCHER = True  # 🔧 Set to True to enable file monitoring

        # Folder monitoring and auto-analysis
        self.folder_watchers = {}  # album_id -> CC_FolderWatcher
        from CC_AutoAnalyzer import CC_AutoAnalyzer
        # Pass database path instead of database object (for thread safety)
        self.auto_analyzer = CC_AutoAnalyzer(self.processor, self.db.db_path)
        self.auto_analyzer.analysis_complete.connect(self._on_auto_analysis_complete)
        self.auto_analyzer.analysis_failed.connect(self._on_auto_analysis_failed)
        self.auto_analyzer.queue_progress.connect(self._update_analysis_progress)
        self.auto_analyzer.status_update.connect(self._update_status)
        self.auto_analyzer.start()
        logger.info("Auto-analyzer started")

        # 3D Renderer
        self.renderer_3d = None
        try:
            from CC_Renderer3D import CC_Renderer3D
            self.renderer_3d = CC_Renderer3D(width=600, height=600)
            logger.info("Taichi 3D renderer initialized")
        except Exception as e:
            logger.warning(f"Taichi renderer not available: {e}")

        # UI Setup
        self.setWindowTitle(f"{CC_PROJECT_NAME} v{CC_VERSION}")
        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1200, 700)

        self._apply_theme()
        self._create_menu()
        self._create_ui()
        self._load_navigator()

        # Restore folder monitoring for existing folder albums
        self._restore_folder_monitoring()

        logger.info("ChromaCloud GUI initialized")

    def _apply_theme(self):
        """Apply macOS Photos-like theme (Light or Dark mode)"""
        palette = QPalette()

        if self.dark_mode:
            # Dark Mode
            bg_color = QColor(0, 0, 0)
            text_color = QColor(255, 255, 255)
            accent_blue = QColor(10, 132, 255)

            palette.setColor(QPalette.Window, bg_color)
            palette.setColor(QPalette.WindowText, text_color)
            palette.setColor(QPalette.Base, QColor(18, 18, 18))
            palette.setColor(QPalette.Text, text_color)
            palette.setColor(QPalette.Button, QColor(48, 48, 48))
            palette.setColor(QPalette.ButtonText, text_color)
            palette.setColor(QPalette.Highlight, accent_blue)
            palette.setColor(QPalette.HighlightedText, text_color)

            self.setStyleSheet("""
                QMainWindow { background-color: #000000; }
                QWidget { background-color: #000000; color: #ffffff; }
                QPushButton {
                    background-color: #303030;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    color: #ffffff;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #3c3c3c; }
                QPushButton:pressed { background-color: #282828; }
                QPushButton:disabled { background-color: #202020; color: #666666; }
                QLabel { color: #ffffff; background-color: transparent; }
                QTreeWidget {
                    background-color: #1c1c1c;
                    border: none;
                    padding: 5px;
                    color: #ffffff;
                }
                QTreeWidget::item { padding: 6px; border-radius: 4px; }
                QTreeWidget::item:hover { background-color: #2c2c2c; }
                QTreeWidget::item:selected { background-color: #0a84ff; color: #ffffff; }
                QGroupBox {
                    border: 1px solid #2c2c2c;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    color: #ffffff;
                }
                QGroupBox::title { color: #98989d; left: 10px; padding: 0 5px; }
                QProgressBar {
                    border: 1px solid #2c2c2c;
                    border-radius: 4px;
                    background-color: #1c1c1c;
                    color: #ffffff;
                }
                QProgressBar::chunk { background-color: #0a84ff; border-radius: 3px; }
                QScrollBar:vertical {
                    background: #000000;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #3a3a3c;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover { background: #4a4a4c; }
            """)
        else:
            # Light Mode
            bg_color = QColor(255, 255, 255)
            text_color = QColor(0, 0, 0)
            accent_blue = QColor(0, 122, 255)

            palette.setColor(QPalette.Window, bg_color)
            palette.setColor(QPalette.WindowText, text_color)
            palette.setColor(QPalette.Base, QColor(250, 250, 250))
            palette.setColor(QPalette.Text, text_color)
            palette.setColor(QPalette.Button, QColor(248, 248, 248))
            palette.setColor(QPalette.ButtonText, text_color)
            palette.setColor(QPalette.Highlight, accent_blue)
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

            self.setStyleSheet("""
                QMainWindow { background-color: #ffffff; }
                QWidget { background-color: #ffffff; color: #000000; }
                QPushButton {
                    background-color: #f8f8f8;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    color: #000000;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #ebebeb; }
                QPushButton:pressed { background-color: #d8d8d8; }
                QPushButton:disabled { background-color: #f8f8f8; color: #999999; }
                QLabel { color: #000000; background-color: transparent; }
                QTreeWidget {
                    background-color: #f6f6f6;
                    border: none;
                    padding: 5px;
                    color: #000000;
                }
                QTreeWidget::item { padding: 6px; border-radius: 4px; }
                QTreeWidget::item:hover { background-color: #e8e8e8; }
                QTreeWidget::item:selected { background-color: #007aff; color: #ffffff; }
                QGroupBox {
                    border: 1px solid #e5e5e5;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    color: #000000;
                }
                QGroupBox::title { color: #8e8e93; left: 10px; padding: 0 5px; }
                QProgressBar {
                    border: 1px solid #e5e5e5;
                    border-radius: 4px;
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QProgressBar::chunk { background-color: #007aff; border-radius: 3px; }
                QScrollBar:vertical {
                    background: #ffffff;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #c7c7cc;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover { background: #aeaeb2; }
            """)

        self.setPalette(palette)

    def _create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        add_folder_album_action = QAction("📁 Add Folder Album...", self)
        add_folder_album_action.setShortcut("Ctrl+Shift+O")
        add_folder_album_action.triggered.connect(self._add_folder_album)
        file_menu.addAction(add_folder_album_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        self.theme_action = QAction("🌙 Dark Mode", self)
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

    def _toggle_theme(self):
        """Toggle between Light and Dark mode"""
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        self.theme_action.setText("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")

    def _create_ui(self):
        """Create main UI with 3-panel layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # LEFT: Navigator
        self.navigator = self._create_navigator()

        # MIDDLE: Photo grid
        self.photo_panel = self._create_photo_panel()

        # RIGHT: Analysis panel
        self.analysis_panel = self._create_analysis_panel()

        splitter.addWidget(self.navigator)
        splitter.addWidget(self.photo_panel)
        splitter.addWidget(self.analysis_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 2)

        main_layout.addWidget(splitter)

    def _create_navigator(self) -> QWidget:
        """Create navigator with Albums"""
        panel = QWidget()
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(400)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel("📂 Albums")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.nav_tree.customContextMenuRequested.connect(self._show_nav_context_menu)
        self.nav_tree.itemClicked.connect(self._on_nav_item_clicked)
        layout.addWidget(self.nav_tree)

        new_album_btn = QPushButton("+ New Album")
        new_album_btn.clicked.connect(self._create_new_album)
        layout.addWidget(new_album_btn)

        return panel

    def _create_photo_panel(self) -> QWidget:
        """Create photo grid panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Store reference for loading controls
        self.photo_panel_layout = layout

        # Header
        header_layout = QHBoxLayout()
        self.photo_header = QLabel("📸 All Photos")
        self.photo_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.photo_header)
        header_layout.addStretch()

        add_btn = QPushButton("+ Add Photos")
        add_btn.clicked.connect(self._add_photos)
        header_layout.addWidget(add_btn)

        batch_btn = QPushButton("⚡ Batch Analyze")
        batch_btn.clicked.connect(self._batch_analyze)
        header_layout.addWidget(batch_btn)

        layout.addLayout(header_layout)

        # Photo grid - VIRTUAL SCROLLING for Photos-like performance! ⚡️⚡️⚡️
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Use virtual photo grid instead of traditional grid
        from CC_VirtualPhotoGrid import SimpleVirtualPhotoGrid
        self.photo_grid_widget = SimpleVirtualPhotoGrid(
            db=self.db,
            thumbnail_class=CC_PhotoThumbnail  # Pass class to avoid circular import
        )
        self.photo_grid_widget.photo_clicked.connect(self._select_photo)
        self.photo_grid = self.photo_grid_widget  # Alias for compatibility

        scroll.setWidget(self.photo_grid_widget)
        layout.addWidget(scroll)

        return panel

    def _create_analysis_panel(self) -> QWidget:
        """Create analysis results panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("🎨 Analysis")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self.current_photo_label = QLabel("No photo selected")
        self.current_photo_label.setStyleSheet("font-size: 10px; color: #999;")
        self.current_photo_label.setWordWrap(True)
        layout.addWidget(self.current_photo_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        self.results_text = QLabel("Select a photo to analyze")
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("color: #333; font-size: 11px; padding: 10px;")
        results_layout.addWidget(self.results_text)
        layout.addWidget(results_group)

        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)

        # Basic stats text (Hue, Sat, Light means)
        self.stats_text = QLabel("No data")
        self.stats_text.setWordWrap(True)
        self.stats_text.setStyleSheet("color: #333; font-size: 11px; font-family: monospace; padding: 10px;")
        stats_layout.addWidget(self.stats_text)

        # Distribution bar charts - horizontal layout (left to right: Hue, Saturation, Lightness)
        # Use minimal spacing like tooltip
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(2)  # Minimal spacing between charts
        charts_layout.setContentsMargins(0, 0, 0, 0)

        self.hue_chart_label = QLabel()
        self.hue_chart_label.setAlignment(Qt.AlignCenter)
        charts_layout.addWidget(self.hue_chart_label)

        self.saturation_chart_label = QLabel()
        self.saturation_chart_label.setAlignment(Qt.AlignCenter)
        charts_layout.addWidget(self.saturation_chart_label)

        self.lightness_chart_label = QLabel()
        self.lightness_chart_label.setAlignment(Qt.AlignCenter)
        charts_layout.addWidget(self.lightness_chart_label)

        stats_layout.addLayout(charts_layout)

        layout.addWidget(stats_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self._analyze_photo)
        btn_layout.addWidget(self.analyze_btn)

        self.visualize_btn = QPushButton("👁️ Visualize")
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self._show_visualization)
        btn_layout.addWidget(self.visualize_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        footer = QLabel(f"ChromaCloud v{CC_VERSION}")
        footer.setStyleSheet("font-size: 9px; color: #666;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        return panel

    def _load_navigator(self):
        """Load albums and folders in separate sections - OPTIMIZED with cache"""
        self.nav_tree.clear()

        # All Photos (root level)
        all_photos = QTreeWidgetItem(self.nav_tree, ["📷 All Photos"])
        all_photos.setData(0, Qt.UserRole, {'type': 'all_photos'})

        # Folders Section (collapsible)
        folders_root = QTreeWidgetItem(self.nav_tree, ["📂 Folders"])
        folders_root.setData(0, Qt.UserRole, {'type': 'section', 'section_name': 'folders'})
        folders_root.setExpanded(True)  # 默认展开

        # Albums Section (collapsible)
        albums_root = QTreeWidgetItem(self.nav_tree, ["📁 Albums"])
        albums_root.setData(0, Qt.UserRole, {'type': 'section', 'section_name': 'albums'})
        albums_root.setExpanded(True)  # 默认展开

        # Load all albums from database
        albums = self.db.get_all_albums()

        folder_count = 0
        album_count = 0

        for album in albums:
            is_folder_album = album.get('folder_path') and album.get('auto_scan')

            if is_folder_album:
                # ⚡️ OPTIMIZED: Use cache for instant loading
                folder_path = Path(album.get('folder_path', ''))

                # Try to load from cache first
                cached_structure = self.db.get_folder_structure(album['id'])

                if cached_structure:
                    # Has cache - instant display
                    photo_count = cached_structure[0]['photo_count'] if cached_structure else album['photo_count']
                else:
                    # No cache - use database value temporarily
                    photo_count = album['photo_count']

                root_item = QTreeWidgetItem(folders_root, [f"📂 {album['name']} ({photo_count})"])
                root_item.setData(0, Qt.UserRole, {
                    'type': 'folder',
                    'id': album['id'],
                    'name': album['name'],
                    'folder_path': str(folder_path),
                    'photo_count': photo_count
                })
                root_item.setToolTip(0, f"Monitoring: {folder_path}")
                root_item.setExpanded(False)  # 默认折叠

                # ⚡️ Build tree from cache (instant)
                if cached_structure:
                    self._build_tree_from_cache(root_item, album['id'], cached_structure)

                # 🔄 Schedule background scan (non-blocking)
                self._schedule_background_scan(album['id'], str(folder_path))

                folder_count += 1
            else:
                # Add to Albums section
                item = QTreeWidgetItem(albums_root, [f"📁 {album['name']} ({album['photo_count']})"])
                item.setData(0, Qt.UserRole, {
                    'type': 'album',
                    'id': album['id'],
                    'name': album['name'],
                    'photo_count': album['photo_count']
                })
                album_count += 1

        # Update section headers with counts
        folders_root.setText(0, f"📂 Folders ({folder_count})")
        albums_root.setText(0, f"📁 Albums ({album_count})")

        # If no folders, hide the section
        if folder_count == 0:
            folders_root.setHidden(True)

        # If no albums, hide the section
        if album_count == 0:
            albums_root.setHidden(True)

    def _build_directory_tree(self, parent_item: QTreeWidgetItem, dir_path: Path, album_id: int, depth: int = 0, max_depth: int = 10):
        """递归构建目录树结构"""
        # 防止过深的递归
        if depth > max_depth:
            return

        # 检查目录是否存在
        if not dir_path.exists() or not dir_path.is_dir():
            return

        try:
            # 统计直接在此目录下的照片（不包括子目录）
            direct_photos = self._count_photos_in_dir_only(dir_path)

            # 如果根目录直接包含照片，显示一个特殊项
            if depth == 0 and direct_photos > 0:
                direct_item = QTreeWidgetItem(parent_item, [f"📷 (根目录照片) ({direct_photos})"])
                direct_item.setData(0, Qt.UserRole, {
                    'type': 'subfolder',
                    'album_id': album_id,
                    'folder_path': str(dir_path),
                    'photo_count': direct_photos,
                    'is_root_direct': True
                })
                direct_item.setToolTip(0, f"直接在 {dir_path} 中的照片")

            # 获取所有子目录，排序
            subdirs = sorted([d for d in dir_path.iterdir()
                            if d.is_dir() and not should_skip_file(d)],
                           key=lambda x: x.name.lower())

            for subdir in subdirs:
                # 跳过隐藏目录和系统目录
                if subdir.name.startswith('.') or subdir.name.startswith('__'):
                    continue

                # 统计此子目录中的照片数量（包括子目录）
                photo_count = self._count_photos_in_dir(subdir)

                if photo_count > 0:  # 只显示有照片的目录
                    # 创建子目录项
                    subdir_item = QTreeWidgetItem(parent_item, [f"📁 {subdir.name} ({photo_count})"])
                    subdir_item.setData(0, Qt.UserRole, {
                        'type': 'subfolder',
                        'album_id': album_id,
                        'folder_path': str(subdir),
                        'photo_count': photo_count
                    })
                    subdir_item.setToolTip(0, str(subdir))
                    subdir_item.setExpanded(False)  # 默认折叠

                    # 递归构建子目录的子目录
                    self._build_directory_tree(subdir_item, subdir, album_id, depth + 1, max_depth)

        except PermissionError:
            # 没有权限访问的目录，跳过
            pass
        except Exception as e:
            logger.warning(f"Error building directory tree for {dir_path}: {e}")

    def _count_photos_in_dir_only(self, dir_path: Path) -> int:
        """统计目录中的照片数量（仅该目录，不包括子目录）"""
        count = 0
        image_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.nef', '.cr2', '.cr3', '.dng',
                           '.JPG', '.JPEG', '.PNG', '.ARW', '.NEF', '.CR2', '.CR3', '.DNG'}

        try:
            for item in dir_path.iterdir():
                if item.is_file() and item.suffix in image_extensions:
                    count += 1
        except (PermissionError, OSError):
            pass

        return count

    def _count_photos_in_dir(self, dir_path: Path) -> int:
        """统计目录中的照片数量（包括子目录）"""
        count = 0
        image_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.nef', '.cr2', '.cr3', '.dng',
                           '.JPG', '.JPEG', '.PNG', '.ARW', '.NEF', '.CR2', '.CR3', '.DNG'}

        try:
            for item in dir_path.rglob('*'):
                if item.is_file() and item.suffix in image_extensions:
                    count += 1
        except (PermissionError, OSError):
            pass

        return count

    # ========== Performance Optimization Methods ==========

    def _build_tree_from_cache(self, parent_item: QTreeWidgetItem,
                               album_id: int, cached_structure: List[dict]):
        """Build directory tree from cache - instant"""
        if not cached_structure:
            return

        # Organize by hierarchy
        path_to_item = {}
        root_path = None

        # Find root path
        for folder_info in cached_structure:
            if folder_info.get('parent_folder_path') is None:
                root_path = folder_info['folder_path']
                break

        for folder_info in cached_structure:
            folder_path = folder_info['folder_path']
            parent_path = folder_info.get('parent_folder_path')
            photo_count = folder_info['photo_count']
            direct_count = folder_info['direct_photo_count']

            if parent_path is None:
                # Root directory's direct photos
                if direct_count > 0:
                    direct_item = QTreeWidgetItem(parent_item,
                        [f"📷 (根目录照片) ({direct_count})"])
                    direct_item.setData(0, Qt.UserRole, {
                        'type': 'subfolder',
                        'album_id': album_id,
                        'folder_path': folder_path,
                        'photo_count': direct_count,
                        'is_root_direct': True
                    })
                path_to_item[folder_path] = parent_item
            else:
                # Subfolder
                folder_name = Path(folder_path).name
                tree_parent = path_to_item.get(parent_path, parent_item)

                folder_item = QTreeWidgetItem(tree_parent,
                    [f"📁 {folder_name} ({photo_count})"])
                folder_item.setData(0, Qt.UserRole, {
                    'type': 'subfolder',
                    'album_id': album_id,
                    'folder_path': folder_path,
                    'photo_count': photo_count
                })
                folder_item.setToolTip(0, folder_path)
                folder_item.setExpanded(False)

                path_to_item[folder_path] = folder_item

    def _schedule_background_scan(self, album_id: int, folder_path: str):
        """Schedule background folder scan (non-blocking)"""
        worker = FolderScanWorker(album_id, folder_path)
        worker.scan_completed.connect(self._on_scan_completed)
        worker.start()

        # Keep reference to prevent garbage collection
        if not hasattr(self, '_scan_workers'):
            self._scan_workers = []
        self._scan_workers.append(worker)

    def _on_scan_completed(self, album_id: int, structure: dict):
        """Background scan completed - update cache and UI"""
        try:
            # Clear old cache
            self.db.clear_folder_cache(album_id)

            # Update cache recursively
            self._update_folder_cache_recursive(album_id, structure)

            # Refresh UI for this album (only if needed)
            self._refresh_album_tree(album_id, structure)

            logger.info(f"Cache updated for album {album_id}")
        except Exception as e:
            logger.error(f"Error updating cache: {e}")

    def _update_folder_cache_recursive(self, album_id: int, structure: dict):
        """Recursively update folder cache"""
        folder_path = structure['path']
        parent_path = structure.get('parent_path')
        total_photos = structure['total_photos']
        direct_photos = structure['direct_photos']

        # Update this folder
        self.db.update_folder_cache(album_id, folder_path, total_photos,
                                    direct_photos, parent_path)

        # Update subdirectories
        for subdir in structure.get('subdirs', []):
            self._update_folder_cache_recursive(album_id, subdir)

    def _refresh_album_tree(self, album_id: int, structure: dict):
        """Refresh album tree in navigator if counts changed"""
        # Find the album item in navigator
        root = self.nav_tree.invisibleRootItem()

        def find_album_item(parent, target_album_id):
            for i in range(parent.childCount()):
                item = parent.child(i)
                data = item.data(0, Qt.UserRole)
                if data and data.get('type') == 'folder' and data.get('id') == target_album_id:
                    return item
                # Recursively search
                result = find_album_item(item, target_album_id)
                if result:
                    return result
            return None

        album_item = find_album_item(root, album_id)
        if album_item:
            data = album_item.data(0, Qt.UserRole)
            old_count = data.get('photo_count', 0)
            new_count = structure['total_photos']

            # Only update if count changed
            if old_count != new_count:
                album_name = data.get('name', 'Unknown')
                album_item.setText(0, f"📂 {album_name} ({new_count})")
                data['photo_count'] = new_count
                album_item.setData(0, Qt.UserRole, data)

                # Clear and rebuild children
                album_item.takeChildren()
                cached_structure = self.db.get_folder_structure(album_id)
                self._build_tree_from_cache(album_item, album_id, cached_structure)

                logger.info(f"Updated album {album_name}: {old_count} -> {new_count} photos")

    def _show_nav_context_menu(self, position):
        """Show context menu for navigator items"""
        item = self.nav_tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        data_type = data.get('type')

        # Don't show menu for section headers or all_photos
        if data_type in ['section', 'all_photos']:
            return

        # Only show menu for albums and folders
        if data_type not in ['album', 'folder']:
            return

        menu = QMenu()

        # Rename action (folders can't be renamed as they're tied to paths)
        if data_type == 'album':
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self._rename_item(item, data))
            menu.addAction(rename_action)

        # Delete action
        delete_text = "Stop Monitoring && Delete" if data_type == 'folder' else "Delete"
        delete_action = QAction(delete_text, self)
        delete_action.triggered.connect(lambda: self._delete_item(item, data))
        menu.addAction(delete_action)

        menu.addSeparator()

        # Statistics action
        stats_action = QAction("View Statistics", self)
        stats_action.triggered.connect(lambda: self._show_statistics(data))
        menu.addAction(stats_action)

        menu.exec(self.nav_tree.viewport().mapToGlobal(position))

    def _create_new_album(self):
        """Create a new album"""
        name, ok = QInputDialog.getText(self, "New Album", "Album name:")
        if ok and name:
            try:
                self.db.create_album(name)
                self._load_navigator()
                QMessageBox.information(self, "Success", f"Album '{name}' created!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create album:\n{e}")

    def _rename_item(self, item, data):
        """Rename album"""
        new_name, ok = QInputDialog.getText(self, "Rename Album", "New name:", text=data['name'])
        if ok and new_name:
            try:
                self.db.rename_album(data['id'], new_name)
                self._load_navigator()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename:\n{e}")

    def _delete_item(self, item, data):
        """Delete album or folder"""
        data_type = data.get('type')
        item_name = data.get('name', 'item')
        item_id = data.get('id')

        if data_type == 'folder':
            message = (f"Stop monitoring and delete folder album '{item_name}'?\n\n"
                      f"This will:\n"
                      f"• Stop file system monitoring\n"
                      f"• Remove the folder from ChromaCloud\n"
                      f"• Keep all analysis data in database\n"
                      f"• NOT delete actual photos from disk")
        else:
            message = f"Delete album '{item_name}'?\n\n(Photos will not be deleted)"

        reply = QMessageBox.question(self, "Confirm Delete", message,
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Stop folder watcher if it's a folder album
                if data_type == 'folder' and item_id in self.folder_watchers:
                    logger.info(f"Stopping folder watcher for album {item_id}")
                    watcher = self.folder_watchers[item_id]
                    watcher.stop_watching()
                    watcher.wait()
                    del self.folder_watchers[item_id]

                # Delete from database
                self.db.delete_album(item_id)
                self._load_navigator()

                QMessageBox.information(self, "Success",
                    f"{'Folder' if data_type == 'folder' else 'Album'} deleted successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{e}")
                logger.error(f"Failed to delete: {e}", exc_info=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{e}")

    def _on_nav_item_clicked(self, item, column):
        """Handle navigator item click"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        data_type = data.get('type')

        if data_type == 'section':
            # Section headers are just for organization, ignore clicks
            return
        elif data_type == 'folder':
            # Folder albums - show all photos in the entire folder
            self._load_album_photos(data['id'])
        elif data_type == 'subfolder':
            # Subfolder - show only photos in this specific subfolder
            self._load_subfolder_photos(data['album_id'], data['folder_path'])
        elif data_type == 'album':
            self._load_album_photos(data['id'])
        elif data_type == 'all_photos':
            self._load_all_photos()

    def _load_album_photos(self, album_id: int):
        """Load photos from an album"""
        self.current_album_id = album_id
        photos = self.db.get_album_photos(album_id)
        self._display_photos([Path(p['file_path']) for p in photos])

        albums = self.db.get_all_albums()
        album_name = next((a['name'] for a in albums if a['id'] == album_id), "Album")
        self.photo_header.setText(f"📁 {album_name} ({len(photos)} photos)")

    def _load_subfolder_photos(self, album_id: int, folder_path: str):
        """Load photos from a specific subfolder - OPTIMIZED to use database only"""
        self.current_album_id = album_id
        folder = Path(folder_path)

        # ⚡️ OPTIMIZED: Load from database only, no filesystem scanning
        # Get all photos in this album
        album_photos = self.db.get_album_photos(album_id)

        # Filter photos that are in this specific subfolder (including subdirectories)
        folder_path_str = str(folder).lower()
        filtered_photos = []

        for photo in album_photos:
            photo_path = Path(photo['file_path'])
            photo_dir_str = str(photo_path.parent).lower()

            # Check if photo is in this folder or its subdirectories
            if photo_dir_str == folder_path_str or photo_dir_str.startswith(folder_path_str + '\\'):
                filtered_photos.append(photo_path)

        # Sort by filename
        filtered_photos.sort(key=lambda x: x.name.lower())

        self._display_photos(filtered_photos)
        self.photo_header.setText(f"📁 {folder.name} ({len(filtered_photos)} photos)")

    def _load_all_photos(self):
        """Load all photos from database - NOT from file system!"""
        self.current_album_id = None

        # ✅ CORRECT: Load from database, NOT file system
        # Only shows photos that have been explicitly added to the database
        photos = self.db.get_all_photos()
        photo_paths = [Path(p['file_path']) for p in photos]

        self._display_photos(photo_paths)
        self.photo_header.setText(f"📷 All Photos ({len(photo_paths)})")


    def _display_photos(self, photo_paths: List[Path]):
        """
        Display photos using VIRTUAL SCROLLING - Photos-like performance! ⚡️⚡️⚡️
        Only creates visible widgets, not all 1106!
        """
        from PySide6.QtCore import QTimer
        import time

        start_time = time.time()

        # Filter out AppleDouble and metadata files
        photo_paths = [p for p in photo_paths if not should_skip_file(p)]

        total_count = len(photo_paths)

        if total_count == 0:
            self.photo_grid_widget.clear()
            return

        # ⚡️ IMPORTANT: Reset thumbnail statistics for this loading session
        # Prevents accumulation across multiple folder views
        CC_PhotoThumbnail._cache_hit_count = 0
        CC_PhotoThumbnail._cache_miss_count = 0
        CC_PhotoThumbnail._cache_hit_time = 0
        CC_PhotoThumbnail._cache_miss_time = 0
        CC_PhotoThumbnail._total_thumbnail_time = 0
        CC_PhotoThumbnail._total_thumbnail_size = 0
        CC_PhotoThumbnail._thumbnail_count = 0
        CC_PhotoThumbnail._thumbnail_samples = []

        # Show loading info
        if total_count > 30:
            logger.info(f"⚡️ Virtual loading {total_count} photos...")
            self._show_loading_controls(total_count)

        # ⚡️ KEY DIFFERENCE: Virtual grid handles everything!
        # It only creates ~30 visible widgets, not all 1106!
        self.photo_grid_widget.set_photos(photo_paths)

        elapsed = time.time() - start_time
        logger.info(f"⚡️ Virtual grid ready in {elapsed*1000:.0f}ms - UI fully responsive!")

        # Update loading controls
        if total_count > 30:
            # Schedule hiding loading controls after background loading completes
            estimated_total_time = total_count * 0.01  # Rough estimate
            QTimer.singleShot(int(estimated_total_time * 1000), self._hide_loading_controls)

        # Report thumbnail statistics
        if total_count > 30:
            QTimer.singleShot(100, lambda: self._report_thumbnail_statistics(total_count))

    # ========== OLD BATCH LOADING METHOD - DEPRECATED ==========
    # Virtual scrolling grid (SimpleVirtualPhotoGrid) now handles all loading
    # This method is no longer called

    def _report_thumbnail_statistics(self, total_count: int):
        """Report thumbnail generation statistics and cache performance"""
        # Cache statistics
        cache_hit_count = getattr(CC_PhotoThumbnail, '_cache_hit_count', 0)
        cache_miss_count = getattr(CC_PhotoThumbnail, '_cache_miss_count', 0)
        cache_hit_time = getattr(CC_PhotoThumbnail, '_cache_hit_time', 0)
        cache_miss_time = getattr(CC_PhotoThumbnail, '_cache_miss_time', 0)

        total_cached = cache_hit_count + cache_miss_count

        if total_cached > 0:
            cache_hit_rate = (cache_hit_count / total_cached) * 100
            avg_cache_hit_time = cache_hit_time / cache_hit_count if cache_hit_count > 0 else 0
            avg_cache_miss_time = cache_miss_time / cache_miss_count if cache_miss_count > 0 else 0

            logger.info(f"")
            logger.info(f"📊 ========== Thumbnail Cache Performance ==========")
            logger.info(f"📊 Total thumbnails loaded: {total_cached}")
            logger.info(f"📊 Cache hits: {cache_hit_count} ({cache_hit_rate:.1f}%)")
            logger.info(f"📊 Cache misses: {cache_miss_count} ({100-cache_hit_rate:.1f}%)")
            logger.info(f"")
            logger.info(f"⚡ Performance:")
            if cache_hit_count > 0:
                logger.info(f"   • Avg cache hit time: {avg_cache_hit_time*1000:.1f}ms ⚡️")
            if cache_miss_count > 0:
                logger.info(f"   • Avg cache miss time: {avg_cache_miss_time*1000:.1f}ms")
            if cache_hit_count > 0 and cache_miss_count > 0:
                speedup = avg_cache_miss_time / avg_cache_hit_time
                logger.info(f"   • Cache speedup: {speedup:.1f}x faster! ⚡️⚡️⚡️")
            logger.info(f"")

            # Time saved by cache
            if cache_hit_count > 0 and cache_miss_count > 0:
                time_without_cache = total_cached * avg_cache_miss_time
                time_with_cache = cache_hit_time + cache_miss_time
                time_saved = time_without_cache - time_with_cache
                logger.info(f"💰 Time Saved by Cache:")
                logger.info(f"   • Would have taken: {time_without_cache:.2f}s (all cache misses)")
                logger.info(f"   • Actually took: {time_with_cache:.2f}s (with {cache_hit_rate:.1f}% cache hits)")
                logger.info(f"   • Time saved: {time_saved:.2f}s ({time_saved/time_without_cache*100:.1f}% faster)")
                logger.info(f"")

        # Generation statistics (for cache misses)
        if hasattr(CC_PhotoThumbnail, '_thumbnail_count') and CC_PhotoThumbnail._thumbnail_count > 0:
            total_time = CC_PhotoThumbnail._total_thumbnail_time
            total_size = CC_PhotoThumbnail._total_thumbnail_size
            count = CC_PhotoThumbnail._thumbnail_count

            avg_time = total_time / count
            avg_size = total_size / count

            logger.info(f"📊 ========== Thumbnail Generation Statistics ==========")
            logger.info(f"📊 New thumbnails generated: {count}")
            logger.info(f"📊 Total generation time: {total_time:.2f}s")
            logger.info(f"📊 Average time per thumbnail: {avg_time*1000:.1f}ms")
            logger.info(f"📊 Total size (JPEG quality=85): {total_size / 1024:.1f} KB ({total_size / 1024 / 1024:.2f} MB)")
            logger.info(f"📊 Average size per thumbnail: {avg_size / 1024:.1f} KB")
            logger.info(f"")
            logger.info(f"💾 Database Storage:")
            logger.info(f"   • For {count} new photos: {total_size / 1024 / 1024:.2f} MB added to cache")
            logger.info(f"   • Cache will save ~{avg_time*1000:.1f}ms per photo on next load")

            # Show some samples
            if hasattr(CC_PhotoThumbnail, '_thumbnail_samples') and CC_PhotoThumbnail._thumbnail_samples:
                logger.info(f"")
                logger.info(f"📸 Sample new thumbnails:")
                for i, sample in enumerate(CC_PhotoThumbnail._thumbnail_samples[:5], 1):
                    logger.info(f"   {i}. {sample['name']}: {sample['time']*1000:.1f}ms, {sample['size']/1024:.1f} KB")

            logger.info(f"")

        # Database cache statistics
        cache_stats = self.db.get_thumbnail_cache_stats()
        if cache_stats['count'] > 0:
            logger.info(f"💾 ========== Database Cache Status ==========")
            logger.info(f"💾 Total cached thumbnails: {cache_stats['count']}")
            logger.info(f"💾 Total cache size: {cache_stats['total_size'] / 1024 / 1024:.2f} MB")
            logger.info(f"💾 Average thumbnail size: {cache_stats['avg_size'] / 1024:.1f} KB")
            logger.info(f"")

        logger.info(f"📊 ====================================================================")
        logger.info(f"")

    def _show_loading_controls(self, total_count: int):
        """Show loading progress and cancel button"""
        if not hasattr(self, '_loading_label'):
            # Create loading label and cancel button at the top
            self._loading_widget = QWidget()
            loading_layout = QHBoxLayout(self._loading_widget)

            self._loading_label = QLabel(f"Loading... 0/{total_count} photos")
            self._loading_label.setStyleSheet("font-weight: bold; color: #0066cc;")
            loading_layout.addWidget(self._loading_label)

            self._cancel_loading_btn = QPushButton("✕ Cancel")
            self._cancel_loading_btn.clicked.connect(self._cancel_loading)
            self._cancel_loading_btn.setMaximumWidth(80)
            loading_layout.addWidget(self._cancel_loading_btn)

            # Insert at position 1 (after header, before scroll area)
            self.photo_panel_layout.insertWidget(1, self._loading_widget)
        else:
            # Widget already exists, just make it visible and update text
            self._loading_label.setText(f"Loading... 0/{total_count} photos")
            self._loading_widget.setVisible(True)

    def _hide_loading_controls(self):
        """Hide loading controls"""
        if hasattr(self, '_loading_widget'):
            self._loading_widget.setVisible(False)

    def _cancel_loading(self):
        """Cancel photo loading - now handled by virtual grid"""
        # Tell virtual grid to cancel background loading
        self.photo_grid_widget.cancel_loading()

        loaded = self.photo_grid.count()
        logger.info(f"⚠️ Loading cancelled by user ({loaded} photos loaded)")
        self._hide_loading_controls()

    def _add_photos(self):
        """Add photos to current album"""
        file_filter = "Images (*.jpg *.jpeg *.png"
        if RAWPY_AVAILABLE:
            file_filter += " *.arw *.nef *.cr2 *.cr3 *.dng"
        file_filter += ")"

        files, _ = QFileDialog.getOpenFileNames(self, "Select Photos", str(Path.home()), file_filter)
        if not files:
            return

        photos_dir = Path(__file__).parent / "Photos"
        photos_dir.mkdir(exist_ok=True)

        for file_path in files:
            src = Path(file_path)
            dst = photos_dir / src.name

            if not dst.exists():
                import shutil
                shutil.copy2(src, dst)

            photo_id = self.db.add_photo(dst)

            if self.current_album_id:
                self.db.add_photo_to_album(photo_id, self.current_album_id)

        if self.current_album_id:
            self._load_album_photos(self.current_album_id)
        else:
            self._load_all_photos()

        self._load_navigator()

    def _select_photo(self, photo_path: Path):
        """Select a photo and load existing analysis if available"""
        self.current_photo = photo_path
        self.current_photo_label.setText(f"Selected:\n{str(photo_path)}")
        self.current_photo_label.setToolTip(str(photo_path))
        self.analyze_btn.setEnabled(True)

        # Try to load existing analysis
        try:
            photo_id = self.db.add_photo(photo_path)
            analysis = self.db.get_analysis(photo_id)

            if analysis and analysis.get('face_detected'):
                logger.info(f"Loading existing analysis for: {photo_path.name}")

                # 自动显示分析结果
                self._display_analysis_results(analysis)

                # 延迟加载：只加载 point cloud，image 和 mask 在点击 Visualize 时才加载
                point_cloud_data = analysis.get('point_cloud_data')
                logger.debug(f"[DEBUG] face_detected={analysis.get('face_detected')}, has point_cloud_data={point_cloud_data is not None}")
                if point_cloud_data:
                    self.point_cloud = pickle.loads(point_cloud_data)
                    # Clear cached image/mask (will be loaded on demand)
                    self.current_photo_rgb = None
                    self.current_mask = None
                    self.visualize_btn.setEnabled(True)
                    logger.info(f"✅ Visualize button ENABLED for {photo_path.name}")
                else:
                    self.visualize_btn.setEnabled(False)
                    logger.warning(f"⚠️ Visualize button DISABLED - no point_cloud_data for {photo_path.name}")
            else:
                # 尚未分析
                logger.info(f"No analysis found for {photo_path.name} - face_detected={analysis.get('face_detected') if analysis else 'N/A'}")
                self.results_text.setText("⏳ Analysis pending or no face detected")
                self.stats_text.setText("Click 'Analyze' button to process this photo")
                self.visualize_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Error loading analysis: {e}")
            self.results_text.setText("❌ Error loading analysis")
            self.stats_text.setText(str(e))

    def _create_distribution_chart(self, values: list, colors: list, title: str, width: float = 0.8, height: float = 2.2) -> QPixmap:
        """Create a vertical stacked bar chart as QPixmap (compact style like tooltip)"""
        fig, ax = plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor('white')

        # Create vertical stacked bar (narrower, like tooltip)
        x = [0]
        bottom = 0
        for val, color in zip(values, colors):
            ax.bar(x, val, bottom=bottom, color=color, width=0.5, edgecolor='white', linewidth=0.5)
            bottom += val

        ax.set_ylim(0, 100)
        ax.set_xlim(-0.5, 0.5)

        # Title at bottom (like tooltip: "Hue", "Sat", "Light")
        ax.set_xlabel(title, fontsize=7, weight='bold')

        ax.set_yticks([])  # No tick labels - everyone knows it's 0-100%
        ax.set_xticks([])

        # Clean up spines - minimal style like tooltip
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False, bottom=False)

        fig.tight_layout(pad=0.1)

        # Convert to QPixmap
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())

        plt.close(fig)

        return pixmap

    def _create_lightness_chart(self, low: float, mid: float, high: float) -> QPixmap:
        """Create lightness distribution bar chart"""
        values = [low, mid, high]
        colors = ['#8B4513', '#CD853F', '#F4A460']  # Brown shades
        return self._create_distribution_chart(values, colors, 'Light')

    def _create_hue_chart(self, very_red: float, red_orange: float, normal: float,
                          yellow: float, very_yellow: float, abnormal: float) -> QPixmap:
        """Create hue distribution bar chart"""
        values = [very_red, red_orange, normal, yellow, very_yellow, abnormal]
        colors = ['#8B0000', '#CD5C5C', '#D2B48C', '#DAA520', '#FFD700', '#696969']
        return self._create_distribution_chart(values, colors, 'Hue')

    def _create_saturation_chart(self, very_low: float, low: float, normal: float,
                                  high: float, very_high: float) -> QPixmap:
        """Create saturation distribution bar chart"""
        values = [very_low, low, normal, high, very_high]
        colors = ['#D3D3D3', '#B0C4DE', '#87CEEB', '#4682B4', '#191970']  # Gray to blue
        return self._create_distribution_chart(values, colors, 'Sat')

    def _display_analysis_results(self, analysis: dict):
        """显示分析结果（包括三个分布图的柱形图版本）"""
        num_points = analysis.get('num_points', 0)
        mask_coverage = analysis.get('mask_coverage', 0)
        h_mean = analysis.get('hue_mean', 0)
        h_std = analysis.get('hue_std', 0)
        s_mean = analysis.get('saturation_mean', 0)
        l_mean = analysis.get('lightness_mean', 0)

        # Lightness 分布 - already in percentage from database
        low_light = analysis.get('lightness_low', 0)
        mid_light = analysis.get('lightness_mid', 0)
        high_light = analysis.get('lightness_high', 0)

        # Hue 分布 - already in percentage from database
        hue_very_red = analysis.get('hue_very_red', 0)
        hue_red_orange = analysis.get('hue_red_orange', 0)
        hue_normal = analysis.get('hue_normal', 0)
        hue_yellow = analysis.get('hue_yellow', 0)
        hue_very_yellow = analysis.get('hue_very_yellow', 0)
        hue_abnormal = analysis.get('hue_abnormal', 0)

        # Saturation 分布 - already in percentage from database
        sat_very_low = analysis.get('sat_very_low', 0)
        sat_low = analysis.get('sat_low', 0)
        sat_normal = analysis.get('sat_normal', 0)
        sat_high = analysis.get('sat_high', 0)
        sat_very_high = analysis.get('sat_very_high', 0)

        self.results_text.setText(
            f"✓ Face detected! (from database)\n{num_points:,} points\nCoverage: {mask_coverage * 100:.1f}%"
        )

        # Display basic statistics as text
        self.stats_text.setText(
            f"Hue: {h_mean:.1f}° ± {h_std:.1f}°\n"
            f"Sat: {s_mean * 100:.1f}%\n"
            f"Light: {l_mean * 100:.1f}%"
        )

        # Create and display distribution bar charts
        lightness_pixmap = self._create_lightness_chart(low_light, mid_light, high_light)
        self.lightness_chart_label.setPixmap(lightness_pixmap)

        hue_pixmap = self._create_hue_chart(hue_very_red, hue_red_orange, hue_normal,
                                              hue_yellow, hue_very_yellow, hue_abnormal)
        self.hue_chart_label.setPixmap(hue_pixmap)

        saturation_pixmap = self._create_saturation_chart(sat_very_low, sat_low, sat_normal,
                                                            sat_high, sat_very_high)
        self.saturation_chart_label.setPixmap(saturation_pixmap)

    def _analyze_photo(self):
        """Analyze selected photo"""
        if not self.current_photo:
            return

        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_text.setText("Processing...")

        thread = CC_ProcessingThread(self.processor, self.current_photo)
        thread.progress.connect(self.progress_bar.setValue)
        thread.finished.connect(self._on_analysis_finished)
        thread.error.connect(self._on_analysis_error)
        thread.start()
        self.processing_thread = thread

    def _on_analysis_finished(self, point_cloud, mask, rgb_image):
        """Handle analysis completion"""
        self.point_cloud = point_cloud
        self.current_photo_rgb = rgb_image
        self.current_mask = mask
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.visualize_btn.setEnabled(True)

        if len(point_cloud) == 0:
            self.results_text.setText("❌ No face detected")
            self.stats_text.setText("No data")
            return

        # Statistics
        h_mean = point_cloud[:, 0].mean()
        h_std = point_cloud[:, 0].std()
        s_mean = point_cloud[:, 1].mean()
        l_mean = point_cloud[:, 2].mean()

        # Calculate lightness distribution
        lightness = point_cloud[:, 2]
        low_light = (lightness < 0.33).sum() / len(lightness) * 100
        mid_light = ((lightness >= 0.33) & (lightness < 0.67)).sum() / len(lightness) * 100
        high_light = (lightness >= 0.67).sum() / len(lightness) * 100

        # Calculate hue distribution
        hue = point_cloud[:, 0]
        hue_very_red = (((hue >= 0) & (hue < 10)) | (hue >= 350)).sum() / len(hue) * 100
        hue_red_orange = ((hue >= 10) & (hue < 20)).sum() / len(hue) * 100
        hue_normal = ((hue >= 20) & (hue < 30)).sum() / len(hue) * 100
        hue_yellow = ((hue >= 30) & (hue < 40)).sum() / len(hue) * 100
        hue_very_yellow = ((hue >= 40) & (hue < 60)).sum() / len(hue) * 100
        hue_abnormal = ((hue >= 60) & (hue < 350)).sum() / len(hue) * 100

        # Calculate saturation distribution
        saturation = point_cloud[:, 1] * 100
        sat_very_low = (saturation < 15).sum() / len(saturation) * 100
        sat_low = ((saturation >= 15) & (saturation < 30)).sum() / len(saturation) * 100
        sat_normal = ((saturation >= 30) & (saturation < 50)).sum() / len(saturation) * 100
        sat_high = ((saturation >= 50) & (saturation < 70)).sum() / len(saturation) * 100
        sat_very_high = (saturation >= 70).sum() / len(saturation) * 100

        self.results_text.setText(
            f"✓ Face detected!\n{len(point_cloud):,} points\nCoverage: {mask.sum() / mask.size * 100:.1f}%"
        )

        # Display basic statistics as text
        self.stats_text.setText(
            f"Hue: {h_mean:.1f}° ± {h_std:.1f}°\n"
            f"Sat: {s_mean * 100:.1f}%\n"
            f"Light: {l_mean * 100:.1f}%"
        )

        # Create and display distribution bar charts
        lightness_pixmap = self._create_lightness_chart(low_light, mid_light, high_light)
        self.lightness_chart_label.setPixmap(lightness_pixmap)

        hue_pixmap = self._create_hue_chart(hue_very_red, hue_red_orange, hue_normal,
                                              hue_yellow, hue_very_yellow, hue_abnormal)
        self.hue_chart_label.setPixmap(hue_pixmap)

        saturation_pixmap = self._create_saturation_chart(sat_very_low, sat_low, sat_normal,
                                                            sat_high, sat_very_high)
        self.saturation_chart_label.setPixmap(saturation_pixmap)

        # Save to database
        try:
            photo_id = self.db.add_photo(self.current_photo)
            results = {
                'face_detected': True,
                'num_points': len(point_cloud),
                'mask_coverage': mask.sum() / mask.size,
                'hue_mean': h_mean,
                'hue_std': h_std,
                'saturation_mean': s_mean,
                'lightness_mean': l_mean,
                'lightness_low': low_light,
                'lightness_mid': mid_light,
                'lightness_high': high_light,
                'hue_very_red': hue_very_red,
                'hue_red_orange': hue_red_orange,
                'hue_normal': hue_normal,
                'hue_yellow': hue_yellow,
                'hue_very_yellow': hue_very_yellow,
                'hue_abnormal': hue_abnormal,
                'sat_very_low': sat_very_low,
                'sat_low': sat_low,
                'sat_normal': sat_normal,
                'sat_high': sat_high,
                'sat_very_high': sat_very_high,
                'point_cloud_data': pickle.dumps(point_cloud)  # Include in results dict
            }
            self.db.save_analysis(photo_id, results)
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")

    def _on_analysis_error(self, error_msg):
        """Handle analysis error"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.results_text.setText(f"❌ Error:\n{error_msg}")
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error_msg}")

    def _batch_analyze(self):
        """Batch analyze all visible photos"""
        photos = []
        for i in range(self.photo_grid.count()):
            widget = self.photo_grid.itemAt(i).widget()
            if isinstance(widget, CC_PhotoThumbnail):
                photos.append(widget.image_path)

        if not photos:
            QMessageBox.warning(self, "No Photos", "No photos to analyze")
            return

        reply = QMessageBox.question(self, "Batch Analysis",
            f"Analyze {len(photos)} photos?", QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        thread = CC_BatchProcessingThread(self.processor, photos)
        thread.progress.connect(lambda p, n: self.progress_bar.setValue(p))
        thread.finished.connect(self._on_batch_finished)
        thread.error.connect(self._on_analysis_error)
        thread.start()
        self.batch_thread = thread

    def _on_batch_finished(self, results):
        """Handle batch processing completion"""
        self.progress_bar.setVisible(False)
        success_count = sum(1 for r in results if r['success'])

        # Save results to database
        for result in results:
            if result['success']:
                try:
                    photo_id = self.db.add_photo(result['path'])

                    analysis_data = {
                        'face_detected': True,
                        'num_points': result['num_points'],
                        'mask_coverage': result['mask_coverage'],
                        'hue_mean': result['hue_mean'],
                        'hue_std': result['hue_std'],
                        'saturation_mean': result['saturation_mean'],
                        'lightness_mean': result['lightness_mean'],
                        'lightness_low': result.get('lightness_low', 0.0),
                        'lightness_mid': result.get('lightness_mid', 0.0),
                        'lightness_high': result.get('lightness_high', 0.0),
                        'hue_very_red': result.get('hue_very_red', 0.0),
                        'hue_red_orange': result.get('hue_red_orange', 0.0),
                        'hue_normal': result.get('hue_normal', 0.0),
                        'hue_yellow': result.get('hue_yellow', 0.0),
                        'hue_very_yellow': result.get('hue_very_yellow', 0.0),
                        'hue_abnormal': result.get('hue_abnormal', 0.0),
                        'sat_very_low': result.get('sat_very_low', 0.0),
                        'sat_low': result.get('sat_low', 0.0),
                        'sat_normal': result.get('sat_normal', 0.0),
                        'sat_high': result.get('sat_high', 0.0),
                        'sat_very_high': result.get('sat_very_high', 0.0),
                        'point_cloud_data': pickle.dumps(result['point_cloud'])  # Include in results dict
                    }
                    self.db.save_analysis(photo_id, analysis_data)
                except Exception as e:
                    logger.error(f"Failed to save result: {e}")

        QMessageBox.information(self, "Batch Complete",
            f"Analyzed {len(results)} photos\nSuccess: {success_count}\nFailed: {len(results) - success_count}")

    def _show_statistics(self, data):
        """Show advanced statistics for album"""
        detailed_stats = self.db.get_album_detailed_statistics(data['id'])

        if not detailed_stats or len(detailed_stats) == 0:
            QMessageBox.information(self, f"Album: {data['name']}",
                "No analysis data available.\n\nPlease analyze some photos first.")
            return

        logger.info(f"Retrieved {len(detailed_stats)} records from database")

        from CC_StatisticsWindow import CC_StatisticsWindow
        stats_window = CC_StatisticsWindow(data['name'], detailed_stats)
        stats_window.show()
        self.stats_window = stats_window

    def _show_visualization(self):
        """Show 3D visualization - with lazy loading of image and mask"""
        if not self.current_photo or self.point_cloud is None:
            QMessageBox.warning(self, "No Data", "No analysis data to visualize")
            return

        # Lazy loading: load image and mask only when needed
        if self.current_photo_rgb is None or self.current_mask is None:
            try:
                logger.info(f"Lazy loading image and mask for visualization: {self.current_photo.name}")
                start_time = time.time()

                # Load image
                image_rgb = self.processor._load_image(self.current_photo)
                self.current_photo_rgb = image_rgb

                # Process to get mask
                _, mask = self.processor.process_image(image_rgb, return_mask=True)
                self.current_mask = mask

                elapsed = time.time() - start_time
                logger.info(f"Lazy loading completed in {elapsed*1000:.0f}ms")

            except Exception as e:
                logger.error(f"Failed to load image/mask for visualization: {e}")
                QMessageBox.critical(self, "Error", f"Failed to load visualization data:\n{e}")
                return

        # Create visualization window
        viz_window = CC_Visualization3DWindow(
            self.current_photo_rgb,
            self.current_mask,
            self.point_cloud,
            self.renderer_3d,
            self.current_photo.name
        )

        # Apply theme to visualization window
        viz_window.setPalette(self.palette())
        viz_window.setStyleSheet(self.styleSheet())

        # Show the window
        viz_window.show()

        # Keep reference so it doesn't get garbage collected
        self.viz_window = viz_window

        logger.info("Visualization window displayed")

    # ========== Folder Album 功能 ==========

    def _restore_folder_monitoring(self):
        """恢复所有 Folder Album 的监控（应用启动时调用）"""
        # ⚠️ Check if folder watching is enabled
        if not self.ENABLE_FOLDER_WATCHER:
            logger.info("⚠️ FolderWatcher is DISABLED - skipping monitoring restoration")
            logger.info("ℹ️  To enable: Set self.ENABLE_FOLDER_WATCHER = True in CC_Main.py")
            return

        try:
            albums = self.db.get_all_albums()
            restored_count = 0

            for album in albums:
                if album.get('folder_path') and album.get('auto_scan'):
                    folder_path = Path(album['folder_path'])

                    # 检查文件夹是否仍然存在
                    if folder_path.exists():
                        logger.info(f"Restoring folder monitoring: {album['name']} -> {folder_path}")
                        self._start_folder_monitoring(album['id'], folder_path)
                        restored_count += 1
                    else:
                        logger.warning(f"Folder no longer exists: {folder_path}")

            if restored_count > 0:
                logger.info(f"Restored monitoring for {restored_count} folder album(s)")
                self.statusBar().showMessage(
                    f"Restored monitoring for {restored_count} folder(s)", 3000
                )
        except Exception as e:
            logger.error(f"Failed to restore folder monitoring: {e}", exc_info=True)

    def _add_folder_album(self):
        """创建一个监控文件夹的 Album"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Monitor",
            str(Path.home())
        )
        if not folder:
            return

        folder_path = Path(folder)
        album_name = folder_path.name

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "Create Folder Album",
            f"Create album '{album_name}' and monitor folder:\n{folder_path}\n\n"
            f"This will:\n"
            f"• Scan all photos in the folder and subfolders\n"
            f"• Automatically analyze all photos in background\n"
            f"• Watch for new photos and analyze them automatically\n\n"
            f"Continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # 创建 Album（保存 folder_path）
            album_id = self.db.create_album(album_name, f"Auto-monitored: {folder_path}")
            cursor = self.db.conn.cursor()
            cursor.execute(
                "UPDATE albums SET folder_path = ?, auto_scan = 1, last_scan_time = CURRENT_TIMESTAMP WHERE id = ?",
                (str(folder_path), album_id)
            )
            self.db.conn.commit()

            # 开始监控和分析
            if self.ENABLE_FOLDER_WATCHER:
                self._start_folder_monitoring(album_id, folder_path)
            else:
                logger.info("⚠️ FolderWatcher is DISABLED - folder monitoring not started")
                logger.info("ℹ️  Photos will be loaded from database only")

            # 刷新 UI
            self._load_navigator()

            logger.info(f"Created folder album: {album_name} -> {folder_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create folder album:\n{e}")
            logger.error(f"Failed to create folder album: {e}", exc_info=True)

    def _start_folder_monitoring(self, album_id: int, folder_path: Path):
        """开始监控文件夹"""
        # ⚠️ Check if folder watching is enabled
        if not self.ENABLE_FOLDER_WATCHER:
            logger.info(f"⚠️ FolderWatcher is DISABLED - skipping monitoring for album {album_id}")
            return

        try:
            from CC_FolderWatcher import CC_FolderWatcher

            # 创建监控器
            watcher = CC_FolderWatcher(folder_path, album_id)
            watcher.new_photos_found.connect(
                lambda paths: self._on_new_photos(album_id, paths)
            )
            watcher.photos_removed.connect(self._on_photos_removed)
            watcher.photos_modified.connect(
                lambda paths: self._on_photos_modified(album_id, paths)
            )
            watcher.scan_progress.connect(self._on_scan_progress)
            watcher.scan_complete.connect(self._on_scan_complete)
            watcher.error.connect(self._on_watcher_error)

            # 启动监控线程（会自动进行初始扫描）
            watcher.start()
            self.folder_watchers[album_id] = watcher

            logger.info(f"Started folder monitoring for album {album_id}: {folder_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start folder monitoring:\n{e}")
            logger.error(f"Failed to start folder monitoring: {e}", exc_info=True)

    def _on_new_photos(self, album_id: int, paths: List[Path]):
        """处理新发现的照片"""
        logger.info(f"[_on_new_photos] New photos detected: {len(paths)} photos for album {album_id}")

        # 添加到自动分析队列
        for path in paths:
            logger.info(f"[_on_new_photos] Adding to analyzer queue: {path.name}")
            self.auto_analyzer.add_photo(path, album_id)

        # 刷新 UI
        logger.info(f"[_on_new_photos] Current album ID: {self.current_album_id}, New photos album ID: {album_id}")

        if self.current_album_id == album_id:
            logger.info(f"[_on_new_photos] Refreshing album photos for album {album_id}")
            self._load_album_photos(album_id)

        logger.info("[_on_new_photos] Refreshing navigator")
        self._load_navigator()

    def _on_photos_removed(self, paths: List[Path]):
        """处理被删除的照片"""
        logger.info(f"Photos removed: {len(paths)} photos")
        # TODO: 可以选择从数据库中删除或标记为已删除
        # 目前保留数据库记录

    def _on_photos_modified(self, album_id: int, paths: List[Path]):
        """处理被修改的照片（例如 Lightroom 重新导出）"""
        logger.info(f"Photos modified: {len(paths)} photos - re-analyzing")

        # 重新分析修改过的照片
        for path in paths:
            self.auto_analyzer.add_photo(path, album_id)

        # 刷新当前显示的照片
        if self.current_photo and self.current_photo in paths:
            self.results_text.setText("⏳ Re-analyzing modified photo...")
            self.stats_text.setText("Please wait...")

    def _on_scan_progress(self, percentage: int, message: str):
        """扫描进度更新"""
        self.statusBar().showMessage(f"Scanning: {message} ({percentage}%)")

    def _on_scan_complete(self, photo_count: int):
        """扫描完成"""
        self.statusBar().showMessage(
            f"Scan complete: {photo_count} photos found. Starting automatic analysis...",
            5000
        )
        logger.info(f"Folder scan complete: {photo_count} photos")

    def _on_watcher_error(self, error_msg: str):
        """文件夹监控错误"""
        QMessageBox.warning(self, "Folder Watcher Error", error_msg)
        logger.error(f"Folder watcher error: {error_msg}")

    # ========== 自动分析相关 ==========

    def _on_auto_analysis_complete(self, photo_id: int, results: dict):
        """单个照片自动分析完成"""
        logger.info(f"Auto-analysis complete for photo_id: {photo_id}")

        # 如果当前正在查看这张照片，刷新显示
        if self.current_photo:
            try:
                current_photo_id = self.db.add_photo(self.current_photo)
                if current_photo_id == photo_id:
                    logger.info("Refreshing display for current photo")
                    self._display_analysis_results(results)

                    # 尝试启用 3D 可视化
                    if results.get('point_cloud_data'):
                        self.point_cloud = pickle.loads(results['point_cloud_data'])
                        self.visualize_btn.setEnabled(True)
            except Exception as e:
                logger.error(f"Error refreshing display: {e}")

    def _on_auto_analysis_failed(self, photo_id: int, error_msg: str):
        """自动分析失败"""
        logger.warning(f"Auto-analysis failed for photo_id {photo_id}: {error_msg}")

    def _update_analysis_progress(self, current: int, total: int):
        """更新分析进度（状态栏）"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.statusBar().showMessage(f"Auto-analyzing: {current}/{total} photos ({percentage}%)")
        else:
            self.statusBar().showMessage("Waiting for photos to analyze...")

    def _update_status(self, message: str):
        """更新状态栏信息"""
        self.statusBar().showMessage(message, 3000)

    def closeEvent(self, event):
        """Clean up on close"""
        # 停止所有文件夹监控
        for album_id, watcher in self.folder_watchers.items():
            logger.info(f"Stopping folder watcher for album {album_id}")
            watcher.stop_watching()
            watcher.wait()

        # 停止自动分析器
        if hasattr(self, 'auto_analyzer'):
            logger.info("Stopping auto-analyzer")
            self.auto_analyzer.stop()
            self.auto_analyzer.wait()

        # 关闭数据库
        self.db.close()
        event.accept()


    # ========== End of CC_MainWindow ==========


# =============================================================================
# Visualization Window
# =============================================================================

class CC_Visualization3DWindow(QWidget):
    """Interactive 3D visualization window with mouse controls"""

    def __init__(self, rgb_image, mask, point_cloud, renderer, photo_name):
        super().__init__()
        self.rgb_image = rgb_image
        self.mask = mask
        self.point_cloud = point_cloud
        self.renderer = renderer
        self.photo_name = photo_name

        # Mouse tracking
        self.last_mouse_pos = None
        self.is_dragging = False

        self.setWindowTitle(f"3D Visualization - {photo_name}")
        self.setGeometry(150, 150, 1400, 800)

        self._create_ui()

    def _create_ui(self):
        """Create the visualization UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🎨 肤色3D圆柱楔形可视化 (拖动鼠标旋转，滚轮缩放)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ECDC4; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Two-column layout
        content_layout = QHBoxLayout()

        # LEFT: Face mask overlay
        left_panel = QGroupBox("检测到的面部遮罩")
        left_layout = QVBoxLayout(left_panel)

        self.face_label = QLabel()
        self.face_label.setAlignment(Qt.AlignCenter)
        self.face_label.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")

        # Create face mask visualization
        import cv2
        overlay = self.rgb_image.copy()

        # Create colored mask overlay (semi-transparent teal)
        mask_colored = np.zeros_like(overlay)
        mask_colored[self.mask == 1] = [78, 205, 196]  # Teal color

        # Blend with original image
        alpha = 0.4
        overlay = cv2.addWeighted(overlay, 1, mask_colored, alpha, 0)

        # Resize to fit display
        h, w = overlay.shape[:2]
        max_size = 500
        if h > max_size or w > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            overlay = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Convert to QPixmap
        h, w, ch = overlay.shape
        bytes_per_line = ch * w
        qt_image = QImage(overlay.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.face_label.setPixmap(pixmap)

        left_layout.addWidget(self.face_label)

        # Mask stats
        mask_info = QLabel(f"遮罩覆盖 {self.mask.sum() / self.mask.size * 100:.2f}% 的图像\n"
                           f"排除: 眼睛、眉毛、嘴唇、面部毛发")
        mask_info.setStyleSheet("color: #999; font-size: 11px; padding: 5px;")
        mask_info.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(mask_info)

        content_layout.addWidget(left_panel)

        # RIGHT: 3D HSL point cloud
        right_panel = QGroupBox("3D HSL 圆柱楔形可视化")
        right_layout = QVBoxLayout(right_panel)

        if self.renderer and len(self.point_cloud) > 0:
            # Upload point cloud data to renderer
            logger.info(f"Uploading {len(self.point_cloud)} points to 3D renderer")
            self.renderer.set_point_cloud(self.point_cloud, color_mode='hsl')

            # Create interactive 3D view
            self.render_label = QLabel()
            self.render_label.setAlignment(Qt.AlignCenter)
            self.render_label.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
            self.render_label.setMinimumSize(600, 600)

            # Enable mouse tracking
            self.render_label.setMouseTracking(True)
            self.render_label.mousePressEvent = self._on_mouse_press
            self.render_label.mouseMoveEvent = self._on_mouse_move
            self.render_label.mouseReleaseEvent = self._on_mouse_release
            self.render_label.wheelEvent = self._on_wheel

            # Initial render
            self._update_render()

            right_layout.addWidget(self.render_label)

            # Controls info
            total_points = len(self.point_cloud)
            displayed_points = min(total_points, self.renderer.max_points)

            if total_points > displayed_points:
                points_info = f"{displayed_points:,} / {total_points:,} 个点已可视化 (受限于最大点数)"
            else:
                points_info = f"{displayed_points:,} 个点已可视化"

            controls_info = QLabel(
                f"{points_info}\n"
                f"🖱️ 左键拖动: 旋转 | 滚轮: 缩放\n"
                f"颜色: HSL 映射到 RGB\n"
                f"⬆️ Y轴: 亮度 (0-100%) | 📐 角度: 色调 | 📏 半径: 饱和度"
            )
            controls_info.setStyleSheet("color: #999; font-size: 11px; padding: 5px;")
            controls_info.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(controls_info)

            # View preset buttons
            view_label = QLabel("快速视角:")
            view_label.setStyleSheet("color: #4ECDC4; font-size: 12px; font-weight: bold; margin-top: 10px;")
            view_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(view_label)

            view_btns_layout = QHBoxLayout()

            front_btn = QPushButton("正面")
            front_btn.setFixedWidth(70)
            front_btn.clicked.connect(lambda: self._set_camera_preset("front"))
            view_btns_layout.addWidget(front_btn)

            side_btn = QPushButton("侧面")
            side_btn.setFixedWidth(70)
            side_btn.clicked.connect(lambda: self._set_camera_preset("side"))
            view_btns_layout.addWidget(side_btn)

            top_btn = QPushButton("俯视")
            top_btn.setFixedWidth(70)
            top_btn.clicked.connect(lambda: self._set_camera_preset("top"))
            view_btns_layout.addWidget(top_btn)

            angle_btn = QPushButton("斜视")
            angle_btn.setFixedWidth(70)
            angle_btn.clicked.connect(lambda: self._set_camera_preset("angle"))
            view_btns_layout.addWidget(angle_btn)

            right_layout.addLayout(view_btns_layout)

        else:
            # Taichi not available or no data
            if not self.renderer:
                info_text = "3D 可视化需要 Taichi\n\n安装: pip install taichi"
            else:
                info_text = "没有点云数据"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("color: #999; padding: 20px;")
            info_label.setAlignment(Qt.AlignCenter)
            right_layout.addWidget(info_label)

        content_layout.addWidget(right_panel)

        layout.addLayout(content_layout)

        # Close button
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedWidth(100)

        # Save screenshot button
        save_btn = QPushButton("💾 保存截图")
        save_btn.clicked.connect(self._save_screenshot)
        save_btn.setFixedWidth(120)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _save_screenshot(self):
        """Save the current 3D render as a screenshot"""
        if not self.renderer:
            return

        try:
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"3D_visualization_{timestamp}.png"

            # Save to output directory
            output_dir = Path(__file__).parent / "output"
            output_dir.mkdir(exist_ok=True)
            filepath = output_dir / filename

            # Save the screenshot
            self.renderer.save_screenshot(str(filepath))

            # Also save the face mask image
            import cv2
            face_filename = f"face_mask_{timestamp}.png"
            face_filepath = output_dir / face_filename

            # Create face mask visualization
            overlay = self.rgb_image.copy()
            mask_colored = np.zeros_like(overlay)
            mask_colored[self.mask == 1] = [78, 205, 196]
            alpha = 0.4
            overlay = cv2.addWeighted(overlay, 1, mask_colored, alpha, 0)
            cv2.imwrite(str(face_filepath), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

            QMessageBox.information(
                self,
                "截图已保存",
                f"3D可视化截图已保存到:\n{filepath}\n\n面部遮罩已保存到:\n{face_filepath}"
            )
            logger.info(f"Screenshots saved: {filepath}, {face_filepath}")

        except Exception as e:
            logger.error(f"Screenshot save error: {e}", exc_info=True)
            QMessageBox.critical(self, "保存失败", f"无法保存截图:\n\n{e}")

    def _update_render(self):
        """Update the 3D render"""
        if not self.renderer:
            return

        try:
            self.renderer.render()
            render_img = self.renderer.get_image()

            h, w, ch = render_img.shape
            bytes_per_line = ch * w
            qt_image = QImage(render_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.render_label.setPixmap(pixmap)

        except Exception as e:
            logger.error(f"Render update error: {e}", exc_info=True)

    def _on_mouse_press(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.pos()

    def _on_mouse_move(self, event):
        """Handle mouse move for rotation"""
        if self.is_dragging and self.last_mouse_pos and self.renderer:
            delta = event.pos() - self.last_mouse_pos

            # Convert pixel movement to rotation angles
            sensitivity = 0.5
            delta_h = delta.x() * sensitivity
            delta_v = -delta.y() * sensitivity  # Invert Y for natural rotation

            # Rotate camera
            self.renderer.rotate_camera(delta_h, delta_v)

            # Update render
            self._update_render()

            self.last_mouse_pos = event.pos()

    def _on_mouse_release(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.last_mouse_pos = None

    def _on_wheel(self, event):
        """Handle mouse wheel for zoom"""
        if self.renderer:
            # Get wheel delta
            delta = event.angleDelta().y()
            zoom_speed = 0.01
            zoom_delta = -delta * zoom_speed  # Negative for natural zoom direction

            # Zoom camera
            self.renderer.zoom_camera(zoom_delta)

            # Update render
            self._update_render()

    def _set_camera_preset(self, preset: str):
        """Set camera to predefined angles"""
        if not self.renderer:
            return

        # Preset angles (horizontal, vertical)
        # Adjusted to make Y-axis (Lightness) appear vertical on screen
        presets = {
            "front": (20, 10),  # Slightly angled front view (Y-axis vertical)
            "side": (90, 10),  # Side view (Y-axis vertical)
            "top": (45, 70),  # Top-down view (looking down at cylinder)
            "angle": (45, 20)  # Angled 3D view (Y-axis mostly vertical)
        }

        if preset in presets:
            h_angle, v_angle = presets[preset]
            self.renderer.set_camera_angles(h_angle, v_angle)

            # Update render
            self._update_render()


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(CC_PROJECT_NAME)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = CC_MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
