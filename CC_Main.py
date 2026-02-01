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
from pathlib import Path
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

from cc_config import CC_PROJECT_NAME, CC_VERSION
from CC_SkinProcessor import CC_SkinProcessor, MEDIAPIPE_AVAILABLE, RAWPY_AVAILABLE
from CC_Database import CC_Database

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CC_MainApp")


# =============================================================================
# Thread Classes
# =============================================================================

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
    """Photo thumbnail widget with proper aspect ratio"""

    def __init__(self, image_path: Path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
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

        self._load_thumbnail()

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

    def _load_thumbnail(self):
        """Load thumbnail preserving aspect ratio"""
        try:
            if self.image_path.suffix.lower() in {'.arw', '.nef', '.cr2', '.cr3', '.dng'}:
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

            # Resize preserving aspect ratio
            img.thumbnail((210, 210), Image.Resampling.LANCZOS)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to QPixmap
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.thumbnail_label.setPixmap(pixmap)

        except Exception as e:
            logger.error(f"Failed to load thumbnail: {e}")
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
        self.db = CC_Database()

        # State
        self.current_photo: Optional[Path] = None
        self.current_album_id: Optional[int] = None
        self.point_cloud: Optional[np.ndarray] = None
        self.current_photo_rgb: Optional[np.ndarray] = None
        self.current_mask: Optional[np.ndarray] = None
        self.dark_mode: bool = False  # Light mode by default

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

        # Photo grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.photo_grid_widget = QWidget()
        self.photo_grid = QGridLayout(self.photo_grid_widget)
        self.photo_grid.setSpacing(10)

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
        self.stats_text = QLabel("No data")
        self.stats_text.setWordWrap(True)
        self.stats_text.setStyleSheet("color: #333; font-size: 11px; font-family: monospace; padding: 10px;")
        stats_layout.addWidget(self.stats_text)
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
        """Load albums and folders in separate sections"""
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
                # Add to Folders section with directory tree structure
                folder_path = Path(album.get('folder_path', ''))

                # 使用实时扫描的照片数量，确保与子目录数量一致
                actual_photo_count = self._count_photos_in_dir(folder_path)

                root_item = QTreeWidgetItem(folders_root, [f"📂 {album['name']} ({actual_photo_count})"])
                root_item.setData(0, Qt.UserRole, {
                    'type': 'folder',
                    'id': album['id'],
                    'name': album['name'],
                    'folder_path': str(folder_path),
                    'photo_count': actual_photo_count
                })
                root_item.setToolTip(0, f"Monitoring: {folder_path}")
                root_item.setExpanded(False)  # 默认折叠

                # 递归构建子目录树
                self._build_directory_tree(root_item, folder_path, album['id'])

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
            subdirs = sorted([d for d in dir_path.iterdir() if d.is_dir()], key=lambda x: x.name.lower())

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
        """Load photos from a specific subfolder"""
        self.current_album_id = album_id
        folder = Path(folder_path)

        if not folder.exists():
            logger.warning(f"Subfolder does not exist: {folder_path}")
            return

        # 获取该文件夹中的所有照片（包括子目录）
        image_extensions = {'.jpg', '.jpeg', '.png', '.arw', '.nef', '.cr2', '.cr3', '.dng',
                           '.JPG', '.JPEG', '.PNG', '.ARW', '.NEF', '.CR2', '.CR3', '.DNG'}

        photos = []
        for item in folder.rglob('*'):
            if item.is_file() and item.suffix in image_extensions:
                photos.append(item)

        photos.sort(key=lambda x: x.name.lower())

        # 过滤出在数据库中的照片（属于这个 album）
        album_photos = self.db.get_album_photos(album_id)
        album_photo_paths = {Path(p['file_path']) for p in album_photos}

        # 只显示既在文件夹中又在数据库中的照片
        filtered_photos = [p for p in photos if p in album_photo_paths]

        self._display_photos(filtered_photos)
        self.photo_header.setText(f"📁 {folder.name} ({len(filtered_photos)} photos)")

    def _load_all_photos(self):
        """Load all photos from Photos folder"""
        self.current_album_id = None
        photos_dir = Path(__file__).parent / "Photos"
        if not photos_dir.exists():
            return

        extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        if RAWPY_AVAILABLE:
            extensions.extend(['*.arw', '*.nef', '*.cr2', '*.cr3', '*.dng'])

        photos = []
        for ext in extensions:
            photos.extend(photos_dir.glob(ext))
        photos.sort()

        self._display_photos(photos)
        self.photo_header.setText(f"📷 All Photos ({len(photos)})")

    def _display_photos(self, photo_paths: List[Path]):
        """Display photos in grid"""
        # Clear grid
        while self.photo_grid.count():
            item = self.photo_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add photos
        row, col = 0, 0
        max_cols = 3

        for photo_path in photo_paths:
            thumbnail = CC_PhotoThumbnail(photo_path)
            thumbnail.mousePressEvent = lambda event, path=photo_path: self._select_photo(path)
            self.photo_grid.addWidget(thumbnail, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

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

                # 加载 point cloud 用于 3D 可视化
                point_cloud_data = analysis.get('point_cloud_data')
                if point_cloud_data:
                    self.point_cloud = pickle.loads(point_cloud_data)
                    try:
                        image_rgb = self.processor._load_image(photo_path)
                        self.current_photo_rgb = image_rgb
                        _, mask = self.processor.process_image(image_rgb, return_mask=True)
                        self.current_mask = mask
                        self.visualize_btn.setEnabled(True)
                    except Exception as e:
                        logger.warning(f"Could not load image for visualization: {e}")
                        self.visualize_btn.setEnabled(False)
                else:
                    self.visualize_btn.setEnabled(False)
            else:
                # 尚未分析
                self.results_text.setText("⏳ Analysis pending or no face detected")
                self.stats_text.setText("Click 'Analyze' button to process this photo")
                self.visualize_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Error loading analysis: {e}")
            self.results_text.setText("❌ Error loading analysis")
            self.stats_text.setText(str(e))

    def _display_analysis_results(self, analysis: dict):
        """显示分析结果（包括三个分布图的文本版本）"""
        num_points = analysis.get('num_points', 0)
        mask_coverage = analysis.get('mask_coverage', 0)
        h_mean = analysis.get('hue_mean', 0)
        h_std = analysis.get('hue_std', 0)
        s_mean = analysis.get('saturation_mean', 0)
        l_mean = analysis.get('lightness_mean', 0)

        # Lightness 分布
        low_light = analysis.get('lightness_low', 0) * 100
        mid_light = analysis.get('lightness_mid', 0) * 100
        high_light = analysis.get('lightness_high', 0) * 100

        # Hue 分布
        hue_very_red = analysis.get('hue_very_red', 0) * 100
        hue_red_orange = analysis.get('hue_red_orange', 0) * 100
        hue_normal = analysis.get('hue_normal', 0) * 100
        hue_yellow = analysis.get('hue_yellow', 0) * 100
        hue_very_yellow = analysis.get('hue_very_yellow', 0) * 100
        hue_abnormal = analysis.get('hue_abnormal', 0) * 100

        # Saturation 分布
        sat_very_low = analysis.get('sat_very_low', 0) * 100
        sat_low = analysis.get('sat_low', 0) * 100
        sat_normal = analysis.get('sat_normal', 0) * 100
        sat_high = analysis.get('sat_high', 0) * 100
        sat_very_high = analysis.get('sat_very_high', 0) * 100

        self.results_text.setText(
            f"✓ Face detected! (from database)\n{num_points:,} points\nCoverage: {mask_coverage * 100:.1f}%"
        )

        self.stats_text.setText(
            f"Hue: {h_mean * 360:.1f}° ± {h_std * 360:.1f}°\n"
            f"Sat: {s_mean * 100:.1f}%\n"
            f"Light: {l_mean * 100:.1f}%\n\n"
            f"📊 Lightness Distribution:\n"
            f"  Low  (<33%): {low_light:.1f}%\n"
            f"  Mid (33-67%): {mid_light:.1f}%\n"
            f"  High (>67%): {high_light:.1f}%\n\n"
            f"🎨 Hue Distribution:\n"
            f"  Very Red (0-10°): {hue_very_red:.1f}%\n"
            f"  Red-Orange (10-25°): {hue_red_orange:.1f}%\n"
            f"  Normal (25-35°): {hue_normal:.1f}%\n"
            f"  Yellow (35-45°): {hue_yellow:.1f}%\n"
            f"  Very Yellow (45-60°): {hue_very_yellow:.1f}%\n"
            f"  Abnormal (>60°): {hue_abnormal:.1f}%\n\n"
            f"💧 Saturation Distribution:\n"
            f"  Very Low (<15%): {sat_very_low:.1f}%\n"
            f"  Low (15-30%): {sat_low:.1f}%\n"
            f"  Normal (30-50%): {sat_normal:.1f}%\n"
            f"  High (50-70%): {sat_high:.1f}%\n"
            f"  Very High (>70%): {sat_very_high:.1f}%"
        )

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

        self.stats_text.setText(
            f"Hue: {h_mean:.1f}° ± {h_std:.1f}°\n"
            f"Sat: {s_mean * 100:.1f}%\n"
            f"Light: {l_mean * 100:.1f}%\n\n"
            f"📊 Lightness Distribution:\n"
            f"  Low  (<33%): {low_light:.1f}%\n"
            f"  Mid (33-67%): {mid_light:.1f}%\n"
            f"  High (>67%): {high_light:.1f}%\n\n"
            f"🎨 Hue Distribution:\n"
            f"  Very Red: {hue_very_red:.1f}%\n"
            f"  Red-Orange: {hue_red_orange:.1f}%\n"
            f"  Normal: {hue_normal:.1f}%\n"
            f"  Yellow: {hue_yellow:.1f}%\n"
            f"  Very Yellow: {hue_very_yellow:.1f}%\n"
            f"  Abnormal: {hue_abnormal:.1f}%\n\n"
            f"💧 Saturation Distribution:\n"
            f"  Very Low: {sat_very_low:.1f}%\n"
            f"  Low: {sat_low:.1f}%\n"
            f"  Normal: {sat_normal:.1f}%\n"
            f"  High: {sat_high:.1f}%\n"
            f"  Very High: {sat_very_high:.1f}%"
        )

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
                'sat_very_high': sat_very_high
            }
            point_cloud_bytes = pickle.dumps(point_cloud)
            self.db.save_analysis(photo_id, results, point_cloud_bytes)
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
                        'sat_very_high': result.get('sat_very_high', 0.0)
                    }
                    point_cloud_bytes = pickle.dumps(result['point_cloud'])
                    self.db.save_analysis(photo_id, analysis_data, point_cloud_bytes)
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
        """Show 3D visualization"""
        if self.current_photo_rgb is None or self.current_mask is None:
            QMessageBox.warning(self, "No Data", "No analysis data to visualize")
            return

        from CC_MainApp import CC_Visualization3DWindow
        viz_window = CC_Visualization3DWindow(
            self.current_photo_rgb, self.current_mask, self.point_cloud,
            self.renderer_3d, self.current_photo.name
        )
        viz_window.setPalette(self.palette())
        viz_window.setStyleSheet(self.styleSheet())
        viz_window.show()
        self.viz_window = viz_window

    # ========== Folder Album 功能 ==========

    def _restore_folder_monitoring(self):
        """恢复所有 Folder Album 的监控（应用启动时调用）"""
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
            self._start_folder_monitoring(album_id, folder_path)

            # 刷新 UI
            self._load_navigator()

            logger.info(f"Created folder album: {album_name} -> {folder_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create folder album:\n{e}")
            logger.error(f"Failed to create folder album: {e}", exc_info=True)

    def _start_folder_monitoring(self, album_id: int, folder_path: Path):
        """开始监控文件夹"""
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
