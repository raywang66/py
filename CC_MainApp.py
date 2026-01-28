"""
ChromaCloud (CC) - Main GUI Application
Author: Senior Software Architect
Date: January 2026

Modern desktop UI for skin tone analysis with macOS-style aesthetics.
Features:
- Photo management (Albums & Projects)
- RAW file support (Sony .arw, Nikon .nef, Canon .cr2, etc.)
- MediaPipe-based face detection
- 3D HSL visualization (when Taichi is available)
- Dual-view comparison mode
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QScrollArea, QGridLayout,
    QSplitter, QGroupBox, QProgressBar, QMessageBox, QListWidget,
    QListWidgetItem, QFrame, QSizePolicy, QTreeWidget, QTreeWidgetItem,
    QInputDialog, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon, QPalette, QColor, QAction

import numpy as np
from PIL import Image

from cc_config import (
    CC_PROJECT_NAME,
    CC_VERSION,
    CC_UI_CONFIG,
    CC_HSL_CONFIG
)
from CC_SkinProcessor import CC_SkinProcessor, MEDIAPIPE_AVAILABLE, RAWPY_AVAILABLE
from CC_Database import CC_Database

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CC_MainApp")


class CC_ProcessingThread(QThread):
    """Background thread for image processing to keep UI responsive"""

    progress = Signal(int)  # Progress percentage
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

            # Load the RGB image first
            image_rgb = self.processor._load_image(self.image_path)
            self.progress.emit(30)

            # Process to get point cloud and mask
            point_cloud, mask = self.processor.process_image(
                image_rgb,
                return_mask=True
            )

            self.progress.emit(100)
            self.finished.emit(point_cloud, mask, image_rgb)

        except Exception as e:
            logger.error(f"Processing error: {e}", exc_info=True)
            self.error.emit(str(e))


class CC_PhotoThumbnail(QFrame):
    """Custom widget for photo thumbnail with metadata"""

    def __init__(self, image_path: Path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setMinimumSize(200, 250)
        self.setMaximumSize(220, 270)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(190, 190)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")

        # Load thumbnail
        self._load_thumbnail()

        # Filename
        filename_label = QLabel(image_path.name)
        filename_label.setWordWrap(True)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet("color: #ddd; font-size: 11px;")

        # File info
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        info_text = f"{image_path.suffix.upper()} • {file_size_mb:.1f} MB"
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 9px;")

        layout.addWidget(self.thumbnail_label)
        layout.addWidget(filename_label)
        layout.addWidget(info_label)

        # Make clickable
        self.setStyleSheet("""
            CC_PhotoThumbnail {
                background-color: #2e2e2e;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }
            CC_PhotoThumbnail:hover {
                border: 2px solid #4ECDC4;
            }
        """)

    def _load_thumbnail(self):
        """Load and display thumbnail"""
        try:
            # Load image (works for both standard and RAW if rawpy is available)
            if self.image_path.suffix.lower() in {'.arw', '.nef', '.cr2', '.cr3', '.dng'}:
                if RAWPY_AVAILABLE:
                    import rawpy
                    with rawpy.imread(str(self.image_path)) as raw:
                        thumb = raw.extract_thumb()
                        if thumb.format == rawpy.ThumbFormat.JPEG:
                            from io import BytesIO
                            img = Image.open(BytesIO(thumb.data))
                        else:
                            # Use postprocessed preview
                            rgb = raw.postprocess(use_camera_wb=True, half_size=True)
                            img = Image.fromarray(rgb)
                else:
                    # RAW not available, show placeholder
                    pixmap = QPixmap(190, 190)
                    pixmap.fill(QColor(42, 42, 42))
                    self.thumbnail_label.setPixmap(pixmap)
                    return
            else:
                img = Image.open(self.image_path)

            # Resize to thumbnail
            img.thumbnail((190, 190), Image.Resampling.LANCZOS)

            # Convert to QPixmap
            if img.mode != 'RGB':
                img = img.convert('RGB')

            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.thumbnail_label.setPixmap(pixmap)

        except Exception as e:
            logger.error(f"Failed to load thumbnail: {e}")
            # Show error placeholder
            pixmap = QPixmap(190, 190)
            pixmap.fill(QColor(80, 42, 42))
            self.thumbnail_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.LeftButton:
            # Emit selection signal (would be connected in main window)
            logger.info(f"Selected: {self.image_path.name}")
            self.setStyleSheet("""
                CC_PhotoThumbnail {
                    background-color: #2e2e2e;
                    border: 2px solid #4ECDC4;
                    border-radius: 8px;
                }
            """)


class CC_MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Initialize processor
        if not MEDIAPIPE_AVAILABLE:
            QMessageBox.critical(
                self,
                "Missing Dependency",
                "MediaPipe is not installed!\n\nInstall with: pip install mediapipe"
            )
            sys.exit(1)

        self.processor = CC_SkinProcessor()
        self.current_photo: Optional[Path] = None
        self.point_cloud: Optional[np.ndarray] = None
        self.current_photo_rgb: Optional[np.ndarray] = None
        self.current_mask: Optional[np.ndarray] = None
        self.processing_thread: Optional[CC_ProcessingThread] = None
        
        # Try to initialize 3D renderer
        self.renderer_3d = None
        try:
            from CC_Renderer3D import CC_Renderer3D
            self.renderer_3d = CC_Renderer3D(width=600, height=600)
            logger.info("Taichi 3D renderer initialized")
        except Exception as e:
            logger.warning(f"Taichi renderer not available: {e}")

        # Setup UI
        self.setWindowTitle(f"{CC_PROJECT_NAME} v{CC_VERSION}")
        self.setGeometry(100, 100, CC_UI_CONFIG.window_width, CC_UI_CONFIG.window_height)
        self.setMinimumSize(CC_UI_CONFIG.window_min_width, CC_UI_CONFIG.window_min_height)

        # Apply dark theme
        self._apply_theme()

        # Create UI
        self._create_ui()

        # Load initial photos
        self._load_photos_from_folder()

        logger.info("ChromaCloud GUI initialized")

    def _apply_theme(self):
        """Apply dark macOS-style theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ToolTipBase, QColor(220, 220, 220))
        palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(78, 205, 196))  # Accent color
        palette.setColor(QPalette.Highlight, QColor(78, 205, 196))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

        self.setPalette(palette)

        # Additional stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ddd;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #4ECDC4;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QLabel {
                color: #ddd;
            }
            QGroupBox {
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #4ECDC4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                background-color: #2a2a2a;
            }
            QProgressBar::chunk {
                background-color: #4ECDC4;
            }
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 5px;
            }
            QScrollArea {
                border: none;
                background-color: #2a2a2a;
            }
        """)

    def _create_ui(self):
        """Create the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # LEFT PANEL: Photo Browser
        left_panel = self._create_photo_browser()

        # RIGHT PANEL: Analysis Results
        right_panel = self._create_analysis_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)  # Photo browser gets more space
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _create_photo_browser(self) -> QWidget:
        """Create photo browser panel"""
        panel = QWidget()
        panel.setMinimumWidth(400)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📸 Photos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ECDC4;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Add Photo button
        add_btn = QPushButton("+ Add Photos")
        add_btn.clicked.connect(self._add_photos)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Photo grid (scrollable)
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

        # Header
        title = QLabel("🎨 Skin Tone Analysis")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4ECDC4;")
        layout.addWidget(title)

        # Current photo info
        self.current_photo_label = QLabel("No photo selected")
        self.current_photo_label.setStyleSheet("font-size: 13px; color: #999;")
        layout.addWidget(self.current_photo_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results group
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QLabel("Select a photo to analyze")
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("color: #ddd; font-size: 12px; padding: 10px;")
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group)

        # Statistics group
        stats_group = QGroupBox("Skin Tone Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_text = QLabel("No data")
        self.stats_text.setWordWrap(True)
        self.stats_text.setStyleSheet("color: #ddd; font-size: 12px; font-family: monospace; padding: 10px;")
        stats_layout.addWidget(self.stats_text)

        layout.addWidget(stats_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self._analyze_current_photo)
        button_layout.addWidget(self.analyze_btn)

        self.visualize_btn = QPushButton("👁️ Visualize")
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self._show_visualization)
        button_layout.addWidget(self.visualize_btn)

        layout.addLayout(button_layout)

        # Second row of buttons
        button_layout2 = QHBoxLayout()

        self.export_btn = QPushButton("💾 Export Data")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_data)
        button_layout2.addWidget(self.export_btn)

        layout.addLayout(button_layout2)

        layout.addStretch()

        # Footer info
        footer = QLabel(f"ChromaCloud v{CC_VERSION}")
        footer.setStyleSheet("font-size: 10px; color: #666;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        return panel

    def _load_photos_from_folder(self):
        """Load photos from the Photos directory"""
        photos_dir = Path(__file__).parent / "Photos"

        if not photos_dir.exists():
            logger.warning("Photos directory not found")
            return

        # Supported extensions
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        if RAWPY_AVAILABLE:
            extensions.extend(['*.arw', '*.nef', '*.cr2', '*.cr3', '*.dng', '*.ARW', '*.NEF', '*.CR2'])

        # Find all photos
        photos = []
        for ext in extensions:
            photos.extend(photos_dir.glob(ext))

        photos.sort()

        # Add to grid
        row, col = 0, 0
        max_cols = 3

        for photo_path in photos:
            thumbnail = CC_PhotoThumbnail(photo_path)
            thumbnail.mousePressEvent = lambda event, path=photo_path: self._select_photo(path)

            self.photo_grid.addWidget(thumbnail, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        logger.info(f"Loaded {len(photos)} photos")

    def _add_photos(self):
        """Open file dialog to add photos"""
        file_filter = "Images (*.jpg *.jpeg *.png"
        if RAWPY_AVAILABLE:
            file_filter += " *.arw *.nef *.cr2 *.cr3 *.dng"
        file_filter += ")"

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Photos",
            str(Path.home()),
            file_filter
        )

        if files:
            # Copy files to Photos directory
            photos_dir = Path(__file__).parent / "Photos"
            photos_dir.mkdir(exist_ok=True)

            for file_path in files:
                src = Path(file_path)
                dst = photos_dir / src.name

                if not dst.exists():
                    import shutil
                    shutil.copy2(src, dst)
                    logger.info(f"Added photo: {src.name}")

            # Reload photo grid
            self._clear_photo_grid()
            self._load_photos_from_folder()

    def _clear_photo_grid(self):
        """Clear all photos from grid"""
        while self.photo_grid.count():
            item = self.photo_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _select_photo(self, photo_path: Path):
        """Handle photo selection"""
        self.current_photo = photo_path
        self.current_photo_label.setText(f"Selected: {photo_path.name}")
        self.analyze_btn.setEnabled(True)
        logger.info(f"Selected photo: {photo_path.name}")

    def _analyze_current_photo(self):
        """Analyze the currently selected photo"""
        if not self.current_photo:
            return

        # Disable button during processing
        self.analyze_btn.setEnabled(False)
        self.visualize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_text.setText("Processing...")

        # Start processing thread
        self.processing_thread = CC_ProcessingThread(self.processor, self.current_photo)
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.finished.connect(self._on_processing_finished)
        self.processing_thread.error.connect(self._on_processing_error)
        self.processing_thread.start()

    def _on_processing_finished(self, point_cloud: np.ndarray, mask: np.ndarray, rgb_image: np.ndarray):
        """Handle processing completion"""
        self.point_cloud = point_cloud
        self.current_photo_rgb = rgb_image
        self.current_mask = mask
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.visualize_btn.setEnabled(True)

        if len(point_cloud) == 0:
            self.results_text.setText("❌ No face detected in the image.\n\nPlease select a photo with a visible face.")
            self.stats_text.setText("No data")
            return

        # Calculate statistics
        h_mean = point_cloud[:, 0].mean()
        h_std = point_cloud[:, 0].std()
        s_mean = point_cloud[:, 1].mean()
        l_mean = point_cloud[:, 2].mean()

        # Display results
        results = f"""
✓ Face detected successfully!

Extracted {len(point_cloud):,} skin tone points

Mask coverage: {mask.sum() / mask.size * 100:.2f}% of image
        """.strip()

        self.results_text.setText(results)

        # Display statistics
        stats = f"""
Hue (H):        {h_mean:.1f}° ± {h_std:.1f}°
                Range: [{CC_HSL_CONFIG.hue_min}°, {CC_HSL_CONFIG.hue_max}°]

Saturation (S): {s_mean * 100:.1f}%
Lightness (L):  {l_mean * 100:.1f}%

Distribution:
  Shadows  (L<30%):  {np.sum(point_cloud[:, 2] < 0.3) / len(point_cloud) * 100:.1f}%
  Midtones (30-70%): {np.sum((point_cloud[:, 2] >= 0.3) & (point_cloud[:, 2] <= 0.7)) / len(point_cloud) * 100:.1f}%
  Highlights (>70%): {np.sum(point_cloud[:, 2] > 0.7) / len(point_cloud) * 100:.1f}%
        """.strip()

        self.stats_text.setText(stats)

        logger.info(f"Analysis complete: {len(point_cloud)} points")

    def _on_processing_error(self, error_msg: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)

        self.results_text.setText(f"❌ Error during processing:\n\n{error_msg}")
        self.stats_text.setText("No data")

        QMessageBox.critical(self, "Processing Error", f"Failed to process image:\n\n{error_msg}")

    def _export_data(self):
        """Export analysis data to CSV"""
        if self.point_cloud is None or len(self.point_cloud) == 0:
            QMessageBox.warning(self, "No Data", "No analysis data to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Data",
            str(Path.home() / f"chromacloud_{self.current_photo.stem}.csv"),
            "CSV Files (*.csv)"
        )

        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Hue (degrees)', 'Saturation (0-1)', 'Lightness (0-1)'])
                    for point in self.point_cloud:
                        writer.writerow(point)

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Analysis data exported to:\n{file_path}"
                )
                logger.info(f"Exported data to: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data:\n\n{e}")

    def _show_visualization(self):
        """Show visualization window with face mask and 3D point cloud"""
        if self.current_photo_rgb is None or self.current_mask is None:
            QMessageBox.warning(self, "No Data", "No analysis data to visualize.")
            return
        
        # Create visualization window
        viz_window = CC_Visualization3DWindow(
            self.current_photo_rgb,
            self.current_mask,
            self.point_cloud,
            self.renderer_3d,
            self.current_photo.name
        )

        # Apply dark theme to visualization window
        viz_window.setPalette(self.palette())
        viz_window.setStyleSheet(self.styleSheet())

        # Show the window
        viz_window.show()

        # Keep reference so it doesn't get garbage collected
        self.viz_window = viz_window

        logger.info("Visualization window displayed")


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
        right_panel = QGroupBox("3D HSL 圆柱楔形 (H: 15-25°)")
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
            controls_info = QLabel(
                f"{len(self.point_cloud):,} 个点已可视化\n"
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
            "front": (20, 10),    # Slightly angled front view (Y-axis vertical)
            "side": (90, 10),     # Side view (Y-axis vertical)
            "top": (45, 70),      # Top-down view (looking down at cylinder)
            "angle": (45, 20)     # Angled 3D view (Y-axis mostly vertical)
        }

        if preset in presets:
            h_angle, v_angle = presets[preset]
            self.renderer.set_camera_angles(h_angle, v_angle)

            # Update render
            self._update_render()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(CC_PROJECT_NAME)

    # Set application-wide font
    from PySide6.QtGui import QFont
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = CC_MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
