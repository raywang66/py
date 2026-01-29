"""
ChromaCloud (CC) - Main GUI Application v2
Author: Senior Software Architect
Date: January 2026

Modern desktop UI for skin tone analysis with Albums & Projects management.
Features:
- Collapsible navigator with Albums/Projects tree
- Batch processing and statistics
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
    QTreeWidgetItem, QInputDialog, QMenu, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QPalette, QColor, QAction

import numpy as np
from PIL import Image
import cv2

from cc_config import CC_PROJECT_NAME, CC_VERSION
from CC_SkinProcessor import CC_SkinProcessor, MEDIAPIPE_AVAILABLE, RAWPY_AVAILABLE
from CC_Database import CC_Database

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CC_MainApp")


class CC_ProcessingThread(QThread):
    """Background thread for image processing"""
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
                        # Calculate lightness distribution
                        lightness = point_cloud[:, 2]
                        low_light = (lightness < 0.33).sum() / len(lightness) * 100
                        mid_light = ((lightness >= 0.33) & (lightness < 0.67)).sum() / len(lightness) * 100
                        high_light = (lightness >= 0.67).sum() / len(lightness) * 100

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
        self.setFrameStyle(QFrame.NoFrame)  # Remove frame
        self.setLineWidth(0)
        self.setFixedSize(220, 270)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Thumbnail with fixed container but preserving aspect ratio
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(210, 210)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: transparent; border: none;")  # No border

        self._load_thumbnail()

        # Filename
        filename_label = QLabel(image_path.name)
        filename_label.setWordWrap(True)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet("color: #000; font-size: 11px; background-color: transparent;")
        filename_label.setMaximumHeight(40)

        layout.addWidget(self.thumbnail_label)
        layout.addWidget(filename_label)

        # macOS Photos style - no borders, clean look
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

            # Set pixmap without scaling (preserves aspect ratio)
            self.thumbnail_label.setPixmap(pixmap)

        except Exception as e:
            logger.error(f"Failed to load thumbnail: {e}")
            pixmap = QPixmap(210, 210)
            pixmap.fill(QColor(245, 245, 245))
            self.thumbnail_label.setPixmap(pixmap)


class CC_MainWindow(QMainWindow):
    """Main application window with collapsible navigator"""

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
        self.current_project_id: Optional[int] = None
        self.point_cloud: Optional[np.ndarray] = None
        self.current_photo_rgb: Optional[np.ndarray] = None
        self.current_mask: Optional[np.ndarray] = None

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
        self._create_ui()
        self._load_navigator()

        logger.info("ChromaCloud v2 GUI initialized")

    def _apply_theme(self):
        """Apply dark theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.Highlight, QColor(78, 205, 196))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QPushButton {
                background-color: #3a3a3a; border: 1px solid #555;
                border-radius: 4px; padding: 8px 16px; color: #ddd;
            }
            QPushButton:hover { background-color: #4a4a4a; border: 1px solid #4ECDC4; }
            QLabel { color: #ddd; }
            QTreeWidget {
                background-color: #2a2a2a; border: 1px solid #3a3a3a;
                border-radius: 4px; padding: 5px;
            }
            QTreeWidget::item { padding: 5px; }
            QTreeWidget::item:hover { background-color: #3a3a3a; }
            QTreeWidget::item:selected { background-color: #4ECDC4; color: black; }
        """)

    def _create_ui(self):
        """Create main UI with 3-panel layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # LEFT: Navigator (collapsible)
        self.navigator = self._create_navigator()

        # MIDDLE: Photo grid
        self.photo_panel = self._create_photo_panel()

        # RIGHT: Analysis panel
        self.analysis_panel = self._create_analysis_panel()

        splitter.addWidget(self.navigator)
        splitter.addWidget(self.photo_panel)
        splitter.addWidget(self.analysis_panel)
        splitter.setStretchFactor(0, 1)  # Navigator
        splitter.setStretchFactor(1, 3)  # Photos
        splitter.setStretchFactor(2, 2)  # Analysis

        main_layout.addWidget(splitter)

    def _create_navigator(self) -> QWidget:
        """Create collapsible navigator with Albums & Projects"""
        panel = QWidget()
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(400)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("📂 Navigator")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ECDC4;")
        layout.addWidget(header)

        # Tree widget
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.nav_tree.customContextMenuRequested.connect(self._show_nav_context_menu)
        self.nav_tree.itemClicked.connect(self._on_nav_item_clicked)
        layout.addWidget(self.nav_tree)

        # Buttons
        btn_layout = QHBoxLayout()

        new_album_btn = QPushButton("+ Album")
        new_album_btn.clicked.connect(self._create_new_album)
        btn_layout.addWidget(new_album_btn)

        new_project_btn = QPushButton("+ Project")
        new_project_btn.clicked.connect(self._create_new_project)
        btn_layout.addWidget(new_project_btn)

        layout.addLayout(btn_layout)

        return panel

    def _create_photo_panel(self) -> QWidget:
        """Create photo grid panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        self.photo_header = QLabel("📸 All Photos")
        self.photo_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ECDC4;")
        header_layout.addWidget(self.photo_header)
        header_layout.addStretch()

        # Buttons
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
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4ECDC4;")
        layout.addWidget(title)

        self.current_photo_label = QLabel("No photo selected")
        self.current_photo_label.setStyleSheet("font-size: 12px; color: #999;")
        layout.addWidget(self.current_photo_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        self.results_text = QLabel("Select a photo to analyze")
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet("color: #ddd; font-size: 11px; padding: 10px;")
        results_layout.addWidget(self.results_text)
        layout.addWidget(results_group)

        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_text = QLabel("No data")
        self.stats_text.setWordWrap(True)
        self.stats_text.setStyleSheet("color: #ddd; font-size: 11px; font-family: monospace; padding: 10px;")
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
        """Load albums and projects into navigator"""
        self.nav_tree.clear()

        # Albums section
        albums_root = QTreeWidgetItem(self.nav_tree, ["📁 Albums"])
        albums_root.setData(0, Qt.UserRole, {'type': 'albums_root'})
        albums = self.db.get_all_albums()
        for album in albums:
            item = QTreeWidgetItem(albums_root, [f"{album['name']} ({album['photo_count']})"])
            item.setData(0, Qt.UserRole, {'type': 'album', 'id': album['id'], 'name': album['name']})
        albums_root.setExpanded(True)

        # Projects section
        projects_root = QTreeWidgetItem(self.nav_tree, ["🗂️ Projects"])
        projects_root.setData(0, Qt.UserRole, {'type': 'projects_root'})
        projects = self.db.get_all_projects()
        for project in projects:
            item = QTreeWidgetItem(projects_root, [f"{project['name']} ({project['photo_count']})"])
            item.setData(0, Qt.UserRole, {'type': 'project', 'id': project['id'], 'name': project['name']})
        projects_root.setExpanded(True)

        # All Photos
        all_photos = QTreeWidgetItem(self.nav_tree, ["📷 All Photos"])
        all_photos.setData(0, Qt.UserRole, {'type': 'all_photos'})

    def _show_nav_context_menu(self, position):
        """Show context menu for navigator items"""
        item = self.nav_tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        menu = QMenu()

        if data['type'] in ['album', 'project']:
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self._rename_item(item, data))
            menu.addAction(rename_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self._delete_item(item, data))
            menu.addAction(delete_action)

            menu.addSeparator()

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

    def _create_new_project(self):
        """Create a new project"""
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        if ok and name:
            try:
                self.db.create_project(name)
                self._load_navigator()
                QMessageBox.information(self, "Success", f"Project '{name}' created!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project:\n{e}")

    def _rename_item(self, item, data):
        """Rename album or project"""
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=data['name'])
        if ok and new_name:
            try:
                if data['type'] == 'album':
                    self.db.rename_album(data['id'], new_name)
                else:
                    self.db.rename_project(data['id'], new_name)
                self._load_navigator()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename:\n{e}")

    def _delete_item(self, item, data):
        """Delete album or project"""
        reply = QMessageBox.question(self, "Confirm Delete",
            f"Delete {data['type']} '{data['name']}'?\n\n(Photos will not be deleted)",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if data['type'] == 'album':
                    self.db.delete_album(data['id'])
                else:
                    self.db.delete_project(data['id'])
                self._load_navigator()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{e}")

    def _on_nav_item_clicked(self, item, column):
        """Handle navigator item click"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data['type'] == 'album':
            self._load_album_photos(data['id'])
        elif data['type'] == 'project':
            self._load_project_photos(data['id'])
        elif data['type'] == 'all_photos':
            self._load_all_photos()

    def _load_album_photos(self, album_id: int):
        """Load photos from an album"""
        self.current_album_id = album_id
        self.current_project_id = None
        photos = self.db.get_album_photos(album_id)
        self._display_photos([Path(p['file_path']) for p in photos])
        self.photo_header.setText(f"📁 Album Photos ({len(photos)})")

    def _load_project_photos(self, project_id: int):
        """Load photos from a project"""
        self.current_project_id = project_id
        self.current_album_id = None
        photos = self.db.get_project_photos(project_id)
        self._display_photos([Path(p['file_path']) for p in photos])
        self.photo_header.setText(f"🗂️ Project Photos ({len(photos)})")

    def _load_all_photos(self):
        """Load all photos from Photos folder"""
        self.current_album_id = None
        self.current_project_id = None
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
        """Add photos to current album/project"""
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

            # Add to database
            photo_id = self.db.add_photo(dst)

            # Add to current album/project if any
            if self.current_album_id:
                self.db.add_photo_to_album(photo_id, self.current_album_id)
            elif self.current_project_id:
                self.db.add_photo_to_project(photo_id, self.current_project_id)

        # Reload
        if self.current_album_id:
            self._load_album_photos(self.current_album_id)
        elif self.current_project_id:
            self._load_project_photos(self.current_project_id)
        else:
            self._load_all_photos()

        self._load_navigator()

    def _select_photo(self, photo_path: Path):
        """Select a photo"""
        self.current_photo = photo_path
        # Show full path instead of just filename
        self.current_photo_label.setText(f"Selected: {str(photo_path)}")
        self.current_photo_label.setToolTip(str(photo_path))  # Also set as tooltip
        self.analyze_btn.setEnabled(True)

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

        # Calculate lightness distribution (Low/Mid/High)
        lightness = point_cloud[:, 2]
        low_light = (lightness < 0.33).sum() / len(lightness) * 100
        mid_light = ((lightness >= 0.33) & (lightness < 0.67)).sum() / len(lightness) * 100
        high_light = (lightness >= 0.67).sum() / len(lightness) * 100

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
            f"  High (>67%): {high_light:.1f}%"
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
                'lightness_high': high_light
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
        # Get current photos
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
                        'lightness_mean': result['lightness_mean']
                    }
                    point_cloud_bytes = pickle.dumps(result['point_cloud'])
                    self.db.save_analysis(photo_id, analysis_data, point_cloud_bytes)
                except Exception as e:
                    logger.error(f"Failed to save result: {e}")

        QMessageBox.information(self, "Batch Complete",
            f"Analyzed {len(results)} photos\nSuccess: {success_count}\nFailed: {len(results) - success_count}")

    def _show_statistics(self, data):
        """Show statistics for album/project"""
        if data['type'] == 'album':
            stats = self.db.get_album_statistics(data['id'])
            title = f"Album: {data['name']}"
        else:
            stats = self.db.get_project_statistics(data['id'])
            title = f"Project: {data['name']}"

        if not stats or stats.get('analyzed_count', 0) == 0:
            QMessageBox.information(self, title, "No analysis data available")
            return

        msg = f"""
Analyzed Photos: {stats['analyzed_count']}

Average Hue: {stats['avg_hue']:.1f}°
Hue Range: {stats['min_hue']:.1f}° - {stats['max_hue']:.1f}°

Average Saturation: {stats['avg_saturation'] * 100:.1f}%
Average Lightness: {stats['avg_lightness'] * 100:.1f}%
        """.strip()

        QMessageBox.information(self, title, msg)

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

    def closeEvent(self, event):
        """Clean up on close"""
        self.db.close()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(CC_PROJECT_NAME)

    from PySide6.QtGui import QFont
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = CC_MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

