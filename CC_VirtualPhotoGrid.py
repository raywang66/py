"""
Virtual Scrolling Photo Grid - Like macOS Photos
Simple but effective implementation
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QGridLayout
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QColor
from pathlib import Path
from typing import List, Optional
import time
import logging

logger = logging.getLogger("CC_VirtualPhotoGrid")


class VirtualPhotoGrid(QWidget):
    """
    Virtual scrolling photo grid - only creates visible widgets
    Like macOS Photos and Lightroom
    """
    photo_clicked = Signal(Path)

    def __init__(self, db=None, thumbnail_class=None, parent=None):
        super().__init__(parent)
        self.photos: List[Path] = []
        self.db = db
        self.thumbnail_class = thumbnail_class  # Store thumbnail class to avoid circular import
        self.thumbnail_widgets = []  # Pool of reusable widgets
        self.visible_range = (0, 0)
        self.cols = 3
        self.row_height = 280  # Height of one row
        self.widget_pool_size = 50  # Pre-create 50 widgets (enough for ~15 rows)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # Container for photos
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(10)

        # Placeholder for scrolling (sets the total scrollable height)
        self.spacer_top = QWidget()
        self.spacer_top.setFixedHeight(0)
        self.container_layout.addWidget(self.spacer_top)

        # Photo grid widget
        from PySide6.QtWidgets import QGridLayout
        self.photo_grid_widget = QWidget()
        self.photo_grid = QGridLayout(self.photo_grid_widget)
        self.photo_grid.setSpacing(10)
        self.container_layout.addWidget(self.photo_grid_widget)

        # Spacer bottom
        self.spacer_bottom = QWidget()
        self.spacer_bottom.setFixedHeight(0)
        self.container_layout.addWidget(self.spacer_bottom)

        self.container_layout.addStretch()

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        # Pre-create widget pool
        self._create_widget_pool()

    def _create_widget_pool(self):
        """Pre-create a pool of reusable thumbnail widgets"""
        if self.thumbnail_class is None:
            logger.warning("⚠️ Thumbnail class not set - skipping widget pool creation")
            return

        # Create empty placeholder widgets
        for _ in range(self.widget_pool_size):
            widget = self.thumbnail_class(Path("placeholder.jpg"), db=self.db)
            widget.setVisible(False)
            self.thumbnail_widgets.append(widget)

    def set_database(self, db):
        """Set database for thumbnail cache"""
        self.db = db
        # Recreate widget pool with db
        self.thumbnail_widgets.clear()
        self._create_widget_pool()

    def set_photos(self, photos: List[Path]):
        """
        Set photos to display - Photos way: instant!
        Only creates visible widgets
        """
        start_time = time.time()

        self.photos = photos
        total_rows = (len(photos) + self.cols - 1) // self.cols
        total_height = total_rows * self.row_height

        # Set virtual height (for scrollbar)
        self.container.setMinimumHeight(total_height + 20)

        # Calculate visible range
        self._update_visible_widgets()

        elapsed = time.time() - start_time
        print(f"⚡️ Virtual grid loaded {len(photos)} photos in {elapsed*1000:.1f}ms!")
        print(f"   Created widgets: {len([w for w in self.thumbnail_widgets if w.isVisible()])}")

    def _update_visible_widgets(self):
        """
        Update visible widgets based on scroll position
        This is called on scroll
        """
        if not self.photos:
            return

        # Calculate visible range
        viewport_height = self.scroll_area.viewport().height()
        scroll_pos = self.scroll_area.verticalScrollBar().value()

        # Which rows are visible?
        first_visible_row = max(0, scroll_pos // self.row_height - 2)  # 2 rows buffer
        last_visible_row = min(
            (len(self.photos) + self.cols - 1) // self.cols,
            (scroll_pos + viewport_height) // self.row_height + 3  # 3 rows buffer
        )

        first_visible_index = first_visible_row * self.cols
        last_visible_index = min(len(self.photos), last_visible_row * self.cols)

        new_range = (first_visible_index, last_visible_index)

        if new_range == self.visible_range:
            return  # No change

        # Update spacers
        self.spacer_top.setFixedHeight(first_visible_row * self.row_height)
        remaining_rows = (len(self.photos) + self.cols - 1) // self.cols - last_visible_row
        self.spacer_bottom.setFixedHeight(remaining_rows * self.row_height)

        # Clear existing widgets
        while self.photo_grid.count():
            item = self.photo_grid.takeAt(0)
            if item.widget():
                item.widget().setVisible(False)

        # Add visible widgets
        widget_index = 0
        for i in range(first_visible_index, last_visible_index):
            if i >= len(self.photos):
                break

            photo_path = self.photos[i]
            row = (i - first_visible_index) // self.cols
            col = (i - first_visible_index) % self.cols

            # Reuse widget from pool
            if widget_index < len(self.thumbnail_widgets):
                widget = self.thumbnail_widgets[widget_index]
                widget.image_path = photo_path
                widget._load_thumbnail()  # Reload thumbnail
                widget.setVisible(True)
                widget.mousePressEvent = lambda event, path=photo_path: self.photo_clicked.emit(path)
                self.photo_grid.addWidget(widget, row, col)
                widget_index += 1

        self.visible_range = new_range

    def _on_scroll(self, value):
        """Handle scroll event - update visible widgets"""
        # Debounce scroll updates
        if not hasattr(self, '_scroll_timer'):
            self._scroll_timer = QTimer()
            self._scroll_timer.setSingleShot(True)
            self._scroll_timer.timeout.connect(self._update_visible_widgets)

        self._scroll_timer.start(50)  # Update after 50ms of no scrolling


class SimpleVirtualPhotoGrid(QWidget):
    """
    Simplified virtual photo grid - loads first batch instantly, rest in background
    Maximum performance with minimal code changes
    """
    photo_clicked = Signal(Path)

    def __init__(self, db=None, thumbnail_class=None, parent=None):
        super().__init__(parent)
        self.photos: List[Path] = []
        self.db = db
        self.thumbnail_class = thumbnail_class  # Store thumbnail class to avoid circular import
        self.cols = 3
        self.widgets_created = 0
        self._loading_cancelled = False

        self.layout = QGridLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def count(self):
        """Return number of widgets (for compatibility)"""
        return self.layout.count()

    def clear(self):
        """Clear all widgets"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.widgets_created = 0

    def set_photos(self, photos: List[Path]):
        """
        Virtual loading - only create first visible batch immediately
        This is the key to Photos-like performance!
        """
        start_time = time.time()

        self.photos = photos
        self._loading_cancelled = False

        # Clear existing
        self.clear()

        if not photos:
            return

        # Ensure thumbnail class is set
        if self.thumbnail_class is None:
            logger.error("⚠️ Thumbnail class not provided - cannot load photos!")
            return

        # Calculate first batch size (visible photos + small buffer)
        # Typical screen shows ~15-20 photos, we load ~30 for smooth scrolling
        first_batch_size = min(30, len(photos))

        logger.info(f"⚡️ Virtual loading: {len(photos)} photos total, loading first {first_batch_size} instantly")

        # Disable updates during batch creation
        self.setUpdatesEnabled(False)

        # Load first batch synchronously (instant!)
        for i in range(first_batch_size):
            photo_path = photos[i]
            row = i // self.cols
            col = i % self.cols

            widget = self.thumbnail_class(photo_path, db=self.db)
            widget.mousePressEvent = lambda event, path=photo_path: self.photo_clicked.emit(path)
            self.layout.addWidget(widget, row, col)
            self.widgets_created += 1

        # Re-enable updates and refresh
        self.setUpdatesEnabled(True)
        self.update()

        elapsed = time.time() - start_time
        logger.info(f"⚡️ First {first_batch_size} photos loaded in {elapsed*1000:.0f}ms - UI ready!")

        # Load rest in background if needed
        if len(photos) > first_batch_size:
            remaining = len(photos) - first_batch_size
            logger.info(f"   Loading remaining {remaining} photos in background...")
            QTimer.singleShot(100, lambda: self._load_remaining(first_batch_size))

    def cancel_loading(self):
        """Cancel background loading"""
        self._loading_cancelled = True
        logger.info("⚠️ Background loading cancelled")

    def _load_remaining(self, start_index):
        """Load remaining photos in background with small batches"""
        if self._loading_cancelled:
            return

        # Adaptive batch size based on total count
        total = len(self.photos)
        if total > 1000:
            batch_size = 15  # Smaller batches for huge libraries
        elif total > 500:
            batch_size = 20
        else:
            batch_size = 30

        end_index = min(start_index + batch_size, len(self.photos))

        # Disable updates during batch
        self.setUpdatesEnabled(False)

        for i in range(start_index, end_index):
            if self._loading_cancelled:
                break

            photo_path = self.photos[i]
            row = i // self.cols
            col = i % self.cols

            widget = self.thumbnail_class(photo_path, db=self.db)
            widget.mousePressEvent = lambda event, path=photo_path: self.photo_clicked.emit(path)
            self.layout.addWidget(widget, row, col)
            self.widgets_created += 1

        # Re-enable updates and refresh
        self.setUpdatesEnabled(True)
        self.update()

        # Continue loading if more photos remain
        if end_index < len(self.photos) and not self._loading_cancelled:
            # Short delay for UI responsiveness
            delay_ms = 40 if total > 1000 else 30
            QTimer.singleShot(delay_ms, lambda: self._load_remaining(end_index))
        else:
            if not self._loading_cancelled:
                logger.info(f"✓ All {len(self.photos)} photos loaded!")

    def addWidget(self, widget, row, col):
        """Add widget to grid (for compatibility)"""
        self.layout.addWidget(widget, row, col)
