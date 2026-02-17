"""
ChromaCloud (CC) - Advanced Statistics Window
Author: Senior Software Architect
Date: January 2026

Professional statistics visualization with multiple chart types.
Clean white background design (macOS Photos style).
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QGroupBox, QGridLayout, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Configure matplotlib for Chinese font support
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

logger = logging.getLogger("CC_Statistics")


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for embedding in Qt"""

    def __init__(self, parent=None, width=8, height=6, dpi=100, is_dark=False):
        # Set colors based on theme
        facecolor = '#0a0a0a' if is_dark else 'white'
        text_color = 'white' if is_dark else 'black'
        grid_color = '#2c2c2c' if is_dark else '#e5e5e5'

        fig = Figure(figsize=(width, height), dpi=dpi, facecolor=facecolor)
        self.axes = fig.add_subplot(111, facecolor=facecolor)

        # Set text colors for dark mode
        if is_dark:
            self.axes.tick_params(colors=text_color, which='both')
            self.axes.xaxis.label.set_color(text_color)
            self.axes.yaxis.label.set_color(text_color)
            self.axes.title.set_color(text_color)
            # Set spine colors
            for spine in self.axes.spines.values():
                spine.set_edgecolor(grid_color)

        super().__init__(fig)
        self.setParent(parent)


class CC_StatisticsWindow(QWidget):
    """Advanced statistics window with multiple visualizations"""

    def __init__(self, album_name: str, stats_data: List[Dict], db=None, is_dark: bool = False):
        super().__init__()
        self.album_name = album_name
        self.stats_data = stats_data
        self.db = db  # Database instance for thumbnail access
        self.is_dark = is_dark

        self.setWindowTitle(f"Statistics - {album_name}")
        self.setGeometry(100, 100, 1400, 900)

        # Apply theme based on mode
        self._apply_theme()
        self._create_ui()
        self._plot_all_charts()

        # Set Windows 11 title bar color to match theme
        self._update_windows_title_bar()

        logger.info(f"Statistics window created for album: {album_name} (Dark mode: {is_dark})")

    def _apply_theme(self):
        """Apply theme (Light or Dark mode) matching main window"""
        if self.is_dark:
            # Dark Mode - macOS Photos style
            self.setStyleSheet("""
                QWidget {
                    background-color: #000000;
                    color: #ffffff;
                    font-family: -apple-system, "Segoe UI", sans-serif;
                }
                QTabWidget::pane {
                    border: 1px solid #2c2c2c;
                    background-color: #000000;
                }
                QTabBar::tab {
                    background-color: #1c1c1c;
                    color: #ffffff;
                    padding: 8px 20px;
                    border: 1px solid #2c2c2c;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #000000;
                    color: #0a84ff;
                    font-weight: 600;
                }
                QTabBar::tab:hover {
                    background-color: #2c2c2c;
                }
                QPushButton {
                    background-color: #0a84ff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0066cc;
                }
                QPushButton:pressed {
                    background-color: #004999;
                }
                QGroupBox {
                    border: 1px solid #2c2c2c;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: #0a0a0a;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #ffffff;
                    font-weight: 600;
                }
                QLabel {
                    color: #ffffff;
                }
                QScrollArea {
                    background-color: #000000;
                    border: none;
                }
            """)
        else:
            # Light Mode - macOS Photos style
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    color: #333333;
                    font-family: -apple-system, "Segoe UI", sans-serif;
                }
                QTabWidget::pane {
                    border: 1px solid #DDDDDD;
                    background-color: white;
                }
                QTabBar::tab {
                    background-color: #F5F5F5;
                    color: #333333;
                    padding: 8px 20px;
                    border: 1px solid #DDDDDD;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    color: #007AFF;
                    font-weight: 600;
                }
                QTabBar::tab:hover {
                    background-color: #EEEEEE;
                }
                QPushButton {
                    background-color: #007AFF;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0051D5;
                }
                QPushButton:pressed {
                    background-color: #003D99;
                }
                QGroupBox {
                    border: 1px solid #DDDDDD;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: #FAFAFA;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                    color: #333333;
                    font-weight: 600;
                }
                QLabel {
                    color: #333333;
                }
            """)

    def _get_plot_bg_color(self):
        """Get plot background color based on theme"""
        return '#0a0a0a' if self.is_dark else '#FAFAFA'

    def _get_text_color(self):
        """Get text color based on theme"""
        return '#ffffff' if self.is_dark else '#333333'

    def _get_grid_color(self):
        """Get grid color based on theme"""
        return '#2c2c2c' if self.is_dark else '#DDDDDD'

    def _apply_plot_theme(self, ax):
        """Apply dark/light theme colors to matplotlib axes"""
        if self.is_dark:
            # Dark mode colors
            text_color = 'white'
            grid_color = '#2c2c2c'

            # Set axis labels color
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)

            # Set title color
            ax.title.set_color(text_color)

            # Set tick labels color
            ax.tick_params(colors=text_color, which='both')

            # Set spine colors
            for spine in ax.spines.values():
                spine.set_edgecolor(grid_color)

            # Set legend colors if legend exists
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor('#1c1c1c')
                legend.get_frame().set_edgecolor(grid_color)
                for text in legend.get_texts():
                    text.set_color(text_color)

    def _update_windows_title_bar(self):
        """Update title bar to match theme (Windows 11 and macOS)"""
        try:
            import platform
            if platform.system() == "Windows":
                from ctypes import windll, c_int, byref
                hwnd = int(self.winId())

                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                DWMWA_CAPTION_COLOR = 35

                if self.is_dark:
                    # Enable dark mode for title bar
                    value = c_int(1)
                    windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(value), 4)
                    # Set caption color to black
                    color = c_int(0x00000000)
                    windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, byref(color), 4)
                else:
                    # Disable dark mode for title bar
                    value = c_int(0)
                    windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(value), 4)
                    # Reset caption color (use system default)
                    color = c_int(0xFFFFFFFF)
                    windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, byref(color), 4)

                logger.info(f"🪟 Statistics Window title bar theme updated: {'Dark' if self.is_dark else 'Light'}")
            elif platform.system() == "Darwin":
                # macOS: Update title bar after window is shown
                self._update_macos_title_bar()
        except Exception as e:
            logger.debug(f"Could not set title bar color: {e}")

    def _update_macos_title_bar(self):
        """Update macOS title bar appearance"""
        try:
            import platform
            if platform.system() != "Darwin":
                return

            # Method 1: Try using objc bridge (if pyobjc is available)
            try:
                import objc
                from ctypes import c_void_p
                from Foundation import NSObject
                from AppKit import NSApp, NSAppearance

                # Get the NSWindow
                ns_view_ptr = int(self.winId())
                ns_view = objc.objc_object(c_void_p=ns_view_ptr)
                ns_window = ns_view.window()

                if ns_window:
                    if self.is_dark:
                        appearance = NSAppearance.appearanceNamed_("NSAppearanceNameDarkAqua")
                    else:
                        appearance = NSAppearance.appearanceNamed_("NSAppearanceNameAqua")

                    ns_window.setAppearance_(appearance)
                    logger.info(f"🍎 Statistics Window title bar updated: {'Dark' if self.is_dark else 'Light'}")
                    return
            except ImportError:
                logger.debug("pyobjc not available for Statistics Window")
            except Exception as e:
                logger.debug(f"objc method failed: {e}")

            # Method 2: ctypes fallback (same as main window)
            try:
                from ctypes import cdll, c_void_p
                import ctypes.util

                appkit_path = ctypes.util.find_library('AppKit')
                if appkit_path:
                    appkit = cdll.LoadLibrary(appkit_path)
                    objc = cdll.LoadLibrary('/usr/lib/libobjc.dylib')

                    objc.objc_getClass.restype = c_void_p
                    objc.sel_registerName.restype = c_void_p
                    objc.objc_msgSend.restype = c_void_p
                    objc.objc_msgSend.argtypes = [c_void_p, c_void_p]

                    ns_view_ptr = int(self.winId())
                    sel_window = objc.sel_registerName(b'window')
                    ns_window = objc.objc_msgSend(c_void_p(ns_view_ptr), sel_window)

                    if ns_window:
                        ns_appearance_class = objc.objc_getClass(b'NSAppearance')
                        appearance_name = b'NSAppearanceNameDarkAqua' if self.is_dark else b'NSAppearanceNameAqua'

                        ns_string_class = objc.objc_getClass(b'NSString')
                        sel_string_with_utf8 = objc.sel_registerName(b'stringWithUTF8String:')
                        objc.objc_msgSend.argtypes = [c_void_p, c_void_p, c_void_p]
                        appearance_name_str = objc.objc_msgSend(ns_string_class, sel_string_with_utf8, appearance_name)

                        sel_appearance_named = objc.sel_registerName(b'appearanceNamed:')
                        appearance = objc.objc_msgSend(ns_appearance_class, sel_appearance_named, appearance_name_str)

                        sel_set_appearance = objc.sel_registerName(b'setAppearance:')
                        objc.objc_msgSend(ns_window, sel_set_appearance, appearance)

                        logger.info(f"🍎 Statistics Window title bar updated (ctypes): {'Dark' if self.is_dark else 'Light'}")
                        return
            except Exception as e:
                logger.debug(f"ctypes method failed: {e}")

        except Exception as e:
            logger.debug(f"macOS title bar update failed: {e}")

    def showEvent(self, event):
        """Handle window show event - update macOS title bar"""
        super().showEvent(event)
        import platform
        if platform.system() == "Darwin":
            self._update_macos_title_bar()

    def _create_ui(self):
        """Create the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel(f"📊 Album Statistics: {self.album_name}")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #333333;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Summary stats
        summary = QLabel(f"{len(self.stats_data)} photos analyzed")
        summary.setFont(QFont("Segoe UI", 12))
        summary.setStyleSheet("color: #666666;")
        header_layout.addWidget(summary)

        layout.addLayout(header_layout)

        # Tab widget for different chart types
        self.tabs = QTabWidget()

        # Most used tabs first - Comparison charts
        # Tab 1: Hue Distribution Comparison (Most frequently used - set as default)
        self.hue_comparison_tab = self._create_chart_tab()
        self.tabs.addTab(self.hue_comparison_tab, "🌈 Hue Comparison")

        # Tab 2: Saturation Distribution Comparison
        self.saturation_comparison_tab = self._create_chart_tab()
        self.tabs.addTab(self.saturation_comparison_tab, "💧 Saturation Comparison")

        # Tab 3: Lightness Distribution Comparison
        self.lightness_tab = self._create_chart_tab()
        self.tabs.addTab(self.lightness_tab, "💡 Lightness Comparison")

        # Additional analysis tabs
        # Tab 4: Overview
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, "📈 Overview")

        # Tab 5: Hue Analysis (old style)
        self.hue_tab = self._create_chart_tab()
        self.tabs.addTab(self.hue_tab, "🎨 Hue Distribution")

        # Tab 6: 3D Scatter
        self.scatter_tab = self._create_chart_tab()
        self.tabs.addTab(self.scatter_tab, "📊 HSL Scatter")

        # Set default tab to Hue Comparison (index 0)
        self.tabs.setCurrentIndex(0)

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        export_btn = QPushButton("💾 Export Report")
        export_btn.clicked.connect(self._export_report)
        btn_layout.addWidget(export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _create_overview_tab(self) -> QWidget:
        """Create overview tab with summary statistics"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QGridLayout(content)

        # Calculate statistics
        hues = [d['hue_mean'] for d in self.stats_data]
        sats = [d['saturation_mean'] for d in self.stats_data]
        lights = [d['lightness_mean'] for d in self.stats_data]

        # Summary statistics groups
        groups = [
            ("Hue (Color Tone)", hues, "°"),
            ("Saturation", [s * 100 for s in sats], "%"),
            ("Lightness", [l * 100 for l in lights], "%")
        ]

        for idx, (name, values, unit) in enumerate(groups):
            group = self._create_stats_group(name, values, unit)
            content_layout.addWidget(group, idx // 2, idx % 2)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return tab

    def _create_stats_group(self, title: str, values: List[float], unit: str) -> QGroupBox:
        """Create a statistics summary group"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        stats = {
            "Mean (Average)": np.mean(values),
            "Median": np.median(values),
            "Std Dev": np.std(values),
            "Min": np.min(values),
            "Max": np.max(values),
            "Range": np.max(values) - np.min(values)
        }

        for stat_name, stat_value in stats.items():
            label = QLabel(f"{stat_name}: {stat_value:.2f}{unit}")
            label.setFont(QFont("Segoe UI", 11))
            layout.addWidget(label)

        return group

    def _create_chart_tab(self) -> QWidget:
        """Create a tab for a chart"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        return tab

    def _plot_all_charts(self):
        """Generate all visualization charts"""
        if not self.stats_data:
            return

        # Extract data
        hues = [d['hue_mean'] for d in self.stats_data]
        sats = [d['saturation_mean'] * 100 for d in self.stats_data]
        lights = [d['lightness_mean'] * 100 for d in self.stats_data]
        photo_names = [d.get('photo_name', f"Photo {i+1}") for i, d in enumerate(self.stats_data)]

        # Plot 1: Hue Distribution Histogram
        self._plot_hue_distribution(self.hue_tab, hues)

        # Plot 2: Hue Distribution Comparison (NEW)
        self._plot_hue_comparison(self.hue_comparison_tab)

        # Plot 3: Saturation Distribution Comparison (NEW)
        self._plot_saturation_comparison(self.saturation_comparison_tab)

        # Plot 4: 3D HSL Scatter
        self._plot_3d_scatter(self.scatter_tab, hues, sats, lights, photo_names)

        # Plot 4: Lightness Distribution
        self._plot_lightness_distribution(self.lightness_tab)

    def _plot_hue_distribution(self, parent_tab: QWidget, hues: List[float]):
        """Plot hue distribution histogram"""
        layout = parent_tab.layout()

        canvas = MplCanvas(parent_tab, width=10, height=6, is_dark=self.is_dark)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        # Plot histogram
        ax = canvas.axes
        ax.hist(hues, bins=20, color='#007AFF', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Hue (degrees)', fontsize=12, weight='bold')
        ax.set_ylabel('Number of Photos', fontsize=12, weight='bold')
        ax.set_title('Hue Distribution Across Album', fontsize=14, weight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor(self._get_plot_bg_color())

        # Add statistics annotations
        mean_hue = np.mean(hues)
        median_hue = np.median(hues)
        ax.axvline(mean_hue, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_hue:.1f}°')
        ax.axvline(median_hue, color='green', linestyle='--', linewidth=2, label=f'Median: {median_hue:.1f}°')
        ax.legend(fontsize=10)

        # Apply dark/light theme colors
        self._apply_plot_theme(ax)

        canvas.figure.tight_layout()

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

    def _plot_3d_scatter(self, parent_tab: QWidget, hues: List[float],
                         sats: List[float], lights: List[float], names: List[str]):
        """Plot 3D HSL scatter plot"""
        layout = parent_tab.layout()

        # Create 3D canvas
        canvas = MplCanvas(parent_tab, width=10, height=8)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        # Remove the old 2D axes and create 3D axes
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111, projection='3d')

        # Convert HSL to RGB for coloring points
        colors = []
        for h, s, l in zip(hues, sats, lights):
            # Normalize values
            h_norm = h / 360.0
            s_norm = s / 100.0
            l_norm = l / 100.0
            # Simple HSL to RGB conversion (approximate)
            r = l_norm + s_norm * (0.5 - abs(l_norm - 0.5))
            g = l_norm
            b = l_norm - s_norm * (0.5 - abs(l_norm - 0.5))
            colors.append((max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b))))

        # Plot scatter
        scatter = ax.scatter(hues, sats, lights, c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=0.5)

        ax.set_xlabel('Hue (degrees)', fontsize=11, weight='bold')
        ax.set_ylabel('Saturation (%)', fontsize=11, weight='bold')
        ax.set_zlabel('Lightness (%)', fontsize=11, weight='bold')
        ax.set_title('3D HSL Distribution', fontsize=14, weight='bold', pad=20)
        ax.set_facecolor(self._get_plot_bg_color())

        canvas.figure.tight_layout()

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

    def _plot_lightness_distribution(self, parent_tab: QWidget):
        """Plot lightness distribution comparison"""
        layout = parent_tab.layout()

        # Extract lightness distribution data if available
        photo_names = []
        photo_paths = []  # Store full paths for hover tooltips
        low_values = []
        mid_values = []
        high_values = []

        logger.info(f"Plotting lightness distribution for {len(self.stats_data)} photos")

        for i, data in enumerate(self.stats_data):
            # Get lightness distribution values first
            low = data.get('lightness_low')
            mid = data.get('lightness_mid')
            high = data.get('lightness_high')

            # Debug log for first few photos
            if i < 3:
                logger.info(f"Photo {i}: low={low}, mid={mid}, high={high}, type={type(low)}")

            # Skip photos without valid data (None or 0.0 means old analysis)
            if low is None or mid is None or high is None:
                logger.warning(f"Photo {i}: Missing lightness data (None)")
                continue

            # Skip if all are 0.0 (old analysis without distribution data)
            if low == 0.0 and mid == 0.0 and high == 0.0:
                logger.warning(f"Photo {i}: Missing lightness data (all zeros)")
                continue

            # Try to convert to float
            try:
                low_val = float(low)
                mid_val = float(mid)
                high_val = float(high)
            except (TypeError, ValueError) as e:
                logger.error(f"Photo {i}: Cannot convert lightness data: {e}")
                continue

            # Only add to arrays if we successfully got the data
            full_name = data.get('photo_name', f"Photo {i+1}")
            file_path = data.get('file_path', '')
            short_name = Path(full_name).stem[:15]  # First 15 chars, no extension
            photo_names.append(short_name)
            photo_paths.append(file_path)
            low_values.append(low_val)
            mid_values.append(mid_val)
            high_values.append(high_val)

        logger.info(f"Successfully extracted data for {len(photo_names)} photos")

        if not photo_names:
            # No valid data
            error_label = QLabel("❌ No lightness distribution data available.\n\n"
                                "Please re-analyze photos to generate this data.")
            error_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            return

        # If we have too many photos, show only a sample
        max_photos_display = 50
        if len(photo_names) > max_photos_display:
            logger.info(f"Too many photos ({len(photo_names)}), sampling {max_photos_display}")
            indices = np.linspace(0, len(photo_names) - 1, max_photos_display, dtype=int)
            photo_names = [photo_names[i] for i in indices]
            photo_paths = [photo_paths[i] for i in indices]
            low_values = [low_values[i] for i in indices]
            mid_values = [mid_values[i] for i in indices]
            high_values = [high_values[i] for i in indices]

        # Adjust canvas size based on number of photos
        width = max(12, len(photo_names) * 0.3)
        canvas = MplCanvas(parent_tab, width=width, height=6, is_dark=self.is_dark)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        ax = canvas.axes

        # Create stacked bar chart
        x = np.arange(len(photo_names))
        width_bar = 0.8

        bars_low = ax.bar(x, low_values, width_bar, label='Low (<33%)', color='#8B4513', alpha=0.8)
        bars_mid = ax.bar(x, mid_values, width_bar, bottom=low_values, label='Mid (33-67%)', color='#CD853F', alpha=0.8)

        # Calculate bottom for high values
        bottom_high = [l + m for l, m in zip(low_values, mid_values)]
        bars_high = ax.bar(x, high_values, width_bar, bottom=bottom_high, label='High (>67%)', color='#F4A460', alpha=0.8)

        ax.set_xlabel('Photos', fontsize=12, weight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=12, weight='bold')
        ax.set_title(f'Lightness Distribution Comparison ({len(photo_names)} photos)',
                     fontsize=14, weight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(photo_names, rotation=60, ha='right', fontsize=8)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_facecolor(self._get_plot_bg_color())
        ax.set_ylim(0, 105)  # Slightly more than 100 for visibility

        # Add interactive hover tooltip with photo preview
        self._add_hover_tooltip(canvas, ax, x, photo_names, photo_paths, bars_low, bars_mid, bars_high)

        canvas.figure.tight_layout()

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

    def _add_hover_tooltip(self, canvas, ax, x_positions, photo_names, photo_paths, *bars):
        """Add interactive hover tooltip with multi-dimensional comparison charts"""
        from PIL import Image
        from io import BytesIO

        # Create a tooltip widget (initially hidden)
        tooltip_widget = QWidget(canvas)
        tooltip_widget.setWindowFlags(Qt.ToolTip)
        tooltip_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """)
        tooltip_layout = QVBoxLayout(tooltip_widget)
        tooltip_layout.setContentsMargins(8, 8, 8, 8)
        tooltip_layout.setSpacing(5)

        # Create labels for content
        photo_label = QLabel()
        chart_label = QLabel()

        tooltip_layout.addWidget(photo_label)
        tooltip_layout.addWidget(chart_label)
        tooltip_widget.hide()

        # Store current bar index
        self.current_bar_index = None

        def on_hover(event):
            """Handle mouse hover event"""
            if event.inaxes != ax:
                # Mouse is outside the axes, hide tooltip
                tooltip_widget.hide()
                self.current_bar_index = None
                return

            # Check which bar the mouse is over
            hovered_bar = None
            for idx, x_pos in enumerate(x_positions):
                # Check if mouse is within the bar's x range
                if abs(event.xdata - x_pos) < 0.4:  # width_bar/2
                    hovered_bar = idx
                    break

            if hovered_bar is not None and hovered_bar != self.current_bar_index:
                self.current_bar_index = hovered_bar
                path = photo_paths[hovered_bar]
                name = photo_names[hovered_bar]

                try:
                    # Get the full photo name (find matching photo in stats_data)
                    full_photo_name = None
                    photo_data = None
                    for data in self.stats_data:
                        data_short_name = Path(data.get('photo_name', '')).stem[:15]
                        if data_short_name == name:
                            full_photo_name = data.get('photo_name', name)
                            photo_data = data
                            break

                    if not photo_data:
                        tooltip_widget.hide()
                        return

                    # Load and display thumbnail
                    # Priority: 1) File if exists, 2) Database thumbnail, 3) Placeholder text
                    pixmap = None

                    if path and Path(path).exists():
                        # Photo file is accessible - load directly
                        img = Image.open(path)
                        img.thumbnail((250, 250), Image.Resampling.LANCZOS)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')

                        buffer = BytesIO()
                        img.save(buffer, format='PNG')
                        buffer.seek(0)

                        pixmap = QPixmap()
                        pixmap.loadFromData(buffer.read())
                    elif self.db:
                        # Photo file not accessible (USB offline) - try database thumbnail
                        try:
                            cached = self.db.get_thumbnail_cache(path)
                            if cached and cached.get('thumbnail_data'):
                                # Load thumbnail from database
                                pixmap = QPixmap()
                                if pixmap.loadFromData(cached['thumbnail_data']):
                                    # Scale to desired size if needed
                                    if pixmap.width() > 250 or pixmap.height() > 250:
                                        pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                    logger.debug(f"Loaded thumbnail from database for offline photo: {full_photo_name}")
                                else:
                                    pixmap = None
                        except Exception as e:
                            logger.debug(f"Could not load thumbnail from database: {e}")
                            pixmap = None

                    if pixmap:
                        photo_label.setPixmap(pixmap)
                    else:
                        # No thumbnail available - show text
                        status = "📷 (offline)" if not Path(path).exists() else "📷"
                        photo_label.setText(f"{status} {full_photo_name}")

                    # Generate mini comparison charts (the other two dimensions)
                    chart_pixmap = self._generate_multi_dim_chart(photo_data, ax)
                    chart_label.setPixmap(chart_pixmap)

                    # Adjust widget size
                    tooltip_widget.adjustSize()

                    # Position tooltip near the cursor
                    cursor_pos = canvas.mapToGlobal(canvas.mapFromParent(canvas.pos()))
                    tooltip_x = cursor_pos.x() + 20
                    tooltip_y = cursor_pos.y() + 20

                    # Make sure tooltip stays on screen
                    screen_geometry = QApplication.primaryScreen().geometry()
                    if tooltip_x + tooltip_widget.width() > screen_geometry.width():
                        tooltip_x = cursor_pos.x() - tooltip_widget.width() - 20
                    if tooltip_y + tooltip_widget.height() > screen_geometry.height():
                        tooltip_y = screen_geometry.height() - tooltip_widget.height() - 20

                    tooltip_widget.move(tooltip_x, tooltip_y)
                    tooltip_widget.show()
                    tooltip_widget.raise_()

                    logger.debug(f"Showing multi-dimensional tooltip for: {name}")
                except Exception as e:
                    logger.error(f"Error creating tooltip: {e}")
                    tooltip_widget.hide()
            elif hovered_bar is None:
                tooltip_widget.hide()
                self.current_bar_index = None

        # Connect the hover event
        canvas.mpl_connect('motion_notify_event', on_hover)
        logger.info("Added multi-dimensional hover tooltip functionality")

    def _generate_multi_dim_chart(self, photo_data: Dict, current_ax) -> QPixmap:
        """Generate mini comparison charts for the other two dimensions"""
        from io import BytesIO

        # Determine which chart we're currently viewing
        current_title = current_ax.get_title().lower()

        # Create a compact figure with 2 mini bar charts (vertical, same width as main chart bars)
        fig = Figure(figsize=(1.5, 2.5), dpi=100, facecolor='white')

        if 'hue' in current_title:
            # Currently viewing Hue, show Saturation and Lightness
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            self._plot_mini_saturation(ax1, photo_data)
            self._plot_mini_lightness(ax2, photo_data)
        elif 'saturation' in current_title:
            # Currently viewing Saturation, show Hue and Lightness
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            self._plot_mini_hue(ax1, photo_data)
            self._plot_mini_lightness(ax2, photo_data)
        elif 'lightness' in current_title:
            # Currently viewing Lightness, show Hue and Saturation
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            self._plot_mini_hue(ax1, photo_data)
            self._plot_mini_saturation(ax2, photo_data)
        else:
            # Default: show all three
            ax1 = fig.add_subplot(1, 3, 1)
            ax2 = fig.add_subplot(1, 3, 2)
            ax3 = fig.add_subplot(1, 3, 3)
            self._plot_mini_hue(ax1, photo_data)
            self._plot_mini_saturation(ax2, photo_data)
            self._plot_mini_lightness(ax3, photo_data)

        fig.tight_layout(pad=0.3)

        # Convert figure to QPixmap
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())

        plt.close(fig)

        return pixmap

    def _plot_mini_hue(self, ax, photo_data: Dict):
        """Plot mini hue distribution chart - vertical stacked bar (no legend)"""
        values = [
            photo_data.get('hue_very_red', 0),
            photo_data.get('hue_red_orange', 0),
            photo_data.get('hue_normal', 0),
            photo_data.get('hue_yellow', 0),
            photo_data.get('hue_very_yellow', 0),
            photo_data.get('hue_abnormal', 0)
        ]
        colors = ['#8B0000', '#CD5C5C', '#D2B48C', '#DAA520', '#FFD700', '#696969']

        # Create vertical stacked bar
        x = [0]
        bottom = 0
        for val, color in zip(values, colors):
            ax.bar(x, val, bottom=bottom, color=color, width=0.6, edgecolor='white', linewidth=0.5)
            bottom += val

        ax.set_ylim(0, 100)
        ax.set_xlim(-0.5, 0.5)
        ax.set_xlabel('Hue', fontsize=7, weight='bold')
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

    def _plot_mini_saturation(self, ax, photo_data: Dict):
        """Plot mini saturation distribution chart - vertical stacked bar (no legend)"""
        values = [
            photo_data.get('sat_very_low', 0),
            photo_data.get('sat_low', 0),
            photo_data.get('sat_normal', 0),
            photo_data.get('sat_high', 0),
            photo_data.get('sat_very_high', 0)
        ]
        colors = ['#D3D3D3', '#B0C4DE', '#87CEEB', '#4682B4', '#191970']

        # Create vertical stacked bar
        x = [0]
        bottom = 0
        for val, color in zip(values, colors):
            ax.bar(x, val, bottom=bottom, color=color, width=0.6, edgecolor='white', linewidth=0.5)
            bottom += val

        ax.set_ylim(0, 100)
        ax.set_xlim(-0.5, 0.5)
        ax.set_xlabel('Sat', fontsize=7, weight='bold')
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

    def _plot_mini_lightness(self, ax, photo_data: Dict):
        """Plot mini lightness distribution chart - vertical stacked bar (no legend)"""
        values = [
            photo_data.get('lightness_low', 0),
            photo_data.get('lightness_mid', 0),
            photo_data.get('lightness_high', 0)
        ]
        colors = ['#8B4513', '#CD853F', '#F4A460']

        # Create vertical stacked bar
        x = [0]
        bottom = 0
        for val, color in zip(values, colors):
            ax.bar(x, val, bottom=bottom, color=color, width=0.6, edgecolor='white', linewidth=0.5)
            bottom += val

        ax.set_ylim(0, 100)
        ax.set_xlim(-0.5, 0.5)
        ax.set_xlabel('Light', fontsize=7, weight='bold')
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

    def _plot_hue_comparison(self, parent_tab: QWidget):
        """Plot hue distribution comparison (similar to lightness distribution)"""
        layout = parent_tab.layout()

        # Extract hue distribution data
        photo_names = []
        photo_paths = []
        very_red_values = []
        red_orange_values = []
        normal_values = []
        yellow_values = []
        very_yellow_values = []
        abnormal_values = []

        logger.info(f"Plotting hue distribution comparison for {len(self.stats_data)} photos")

        for i, data in enumerate(self.stats_data):
            # Get hue distribution values
            very_red = data.get('hue_very_red')
            red_orange = data.get('hue_red_orange')
            normal = data.get('hue_normal')
            yellow = data.get('hue_yellow')
            very_yellow = data.get('hue_very_yellow')
            abnormal = data.get('hue_abnormal')

            # Skip photos without valid data
            if any(v is None for v in [very_red, red_orange, normal, yellow, very_yellow, abnormal]):
                logger.warning(f"Photo {i}: Missing hue distribution data (None)")
                continue

            # Skip if all are 0.0 (old analysis without distribution data)
            if all(v == 0.0 for v in [very_red, red_orange, normal, yellow, very_yellow, abnormal]):
                logger.warning(f"Photo {i}: Missing hue distribution data (all zeros)")
                continue

            # Try to convert to float
            try:
                very_red_val = float(very_red)
                red_orange_val = float(red_orange)
                normal_val = float(normal)
                yellow_val = float(yellow)
                very_yellow_val = float(very_yellow)
                abnormal_val = float(abnormal)
            except (TypeError, ValueError) as e:
                logger.error(f"Photo {i}: Cannot convert hue distribution data: {e}")
                continue

            # Add to arrays
            full_name = data.get('photo_name', f"Photo {i+1}")
            file_path = data.get('file_path', '')
            short_name = Path(full_name).stem[:15]  # First 15 chars, no extension
            photo_names.append(short_name)
            photo_paths.append(file_path)
            very_red_values.append(very_red_val)
            red_orange_values.append(red_orange_val)
            normal_values.append(normal_val)
            yellow_values.append(yellow_val)
            very_yellow_values.append(very_yellow_val)
            abnormal_values.append(abnormal_val)

        logger.info(f"Successfully extracted hue data for {len(photo_names)} photos")

        if not photo_names:
            # No valid data
            error_label = QLabel("❌ No hue distribution data available.\n\n"
                                "Please re-analyze photos to generate this data.")
            error_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            return

        # If we have too many photos, show only a sample
        max_photos_display = 50
        if len(photo_names) > max_photos_display:
            logger.info(f"Too many photos ({len(photo_names)}), sampling {max_photos_display}")
            indices = np.linspace(0, len(photo_names) - 1, max_photos_display, dtype=int)
            photo_names = [photo_names[i] for i in indices]
            photo_paths = [photo_paths[i] for i in indices]
            very_red_values = [very_red_values[i] for i in indices]
            red_orange_values = [red_orange_values[i] for i in indices]
            normal_values = [normal_values[i] for i in indices]
            yellow_values = [yellow_values[i] for i in indices]
            very_yellow_values = [very_yellow_values[i] for i in indices]
            abnormal_values = [abnormal_values[i] for i in indices]

        # Adjust canvas size based on number of photos
        width = max(12, len(photo_names) * 0.3)
        canvas = MplCanvas(parent_tab, width=width, height=6, is_dark=self.is_dark)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        ax = canvas.axes

        # Create stacked bar chart with professional skin tone colors
        x = np.arange(len(photo_names))
        width_bar = 0.8

        # Define colors for each hue range (using appropriate colors)
        bars_very_red = ax.bar(x, very_red_values, width_bar, label='Very Red (0-10°, 350-360°)',
                               color='#8B0000', alpha=0.8)

        bars_red_orange = ax.bar(x, red_orange_values, width_bar, bottom=very_red_values,
                                  label='Red-Orange (10-20°)', color='#CD5C5C', alpha=0.8)

        bottom_normal = [vr + ro for vr, ro in zip(very_red_values, red_orange_values)]
        bars_normal = ax.bar(x, normal_values, width_bar, bottom=bottom_normal,
                             label='Normal (20-30°)', color='#D2B48C', alpha=0.8)

        bottom_yellow = [b + n for b, n in zip(bottom_normal, normal_values)]
        bars_yellow = ax.bar(x, yellow_values, width_bar, bottom=bottom_yellow,
                             label='Yellow (30-40°)', color='#DAA520', alpha=0.8)

        bottom_very_yellow = [b + y for b, y in zip(bottom_yellow, yellow_values)]
        bars_very_yellow = ax.bar(x, very_yellow_values, width_bar, bottom=bottom_very_yellow,
                                   label='Very Yellow (40-60°)', color='#FFD700', alpha=0.8)

        bottom_abnormal = [b + vy for b, vy in zip(bottom_very_yellow, very_yellow_values)]
        bars_abnormal = ax.bar(x, abnormal_values, width_bar, bottom=bottom_abnormal,
                               label='Abnormal (60-350°)', color='#696969', alpha=0.8)

        ax.set_xlabel('Photos', fontsize=12, weight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=12, weight='bold')
        ax.set_title(f'Hue Distribution Comparison ({len(photo_names)} photos)',
                     fontsize=14, weight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(photo_names, rotation=60, ha='right', fontsize=8)
        ax.legend(loc='upper right', fontsize=9, ncol=2)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_facecolor(self._get_plot_bg_color())
        ax.set_ylim(0, 105)  # Slightly more than 100 for visibility

        # Apply dark/light theme colors
        self._apply_plot_theme(ax)

        # Add interactive hover tooltip with photo preview
        self._add_hover_tooltip(canvas, ax, x, photo_names, photo_paths,
                                bars_very_red, bars_red_orange, bars_normal,
                                bars_yellow, bars_very_yellow, bars_abnormal)

        canvas.figure.tight_layout()

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

    def _plot_saturation_comparison(self, parent_tab: QWidget):
        """Plot saturation distribution comparison"""
        layout = parent_tab.layout()

        # Extract saturation distribution data
        photo_names = []
        photo_paths = []
        very_low_values = []
        low_values = []
        normal_values = []
        high_values = []
        very_high_values = []

        logger.info(f"Plotting saturation distribution comparison for {len(self.stats_data)} photos")

        for i, data in enumerate(self.stats_data):
            # Get saturation distribution values
            very_low = data.get('sat_very_low')
            low = data.get('sat_low')
            normal = data.get('sat_normal')
            high = data.get('sat_high')
            very_high = data.get('sat_very_high')

            # Skip photos without valid data
            if any(v is None for v in [very_low, low, normal, high, very_high]):
                logger.warning(f"Photo {i}: Missing saturation distribution data (None)")
                continue

            # Skip if all are 0.0 (old analysis without distribution data)
            if all(v == 0.0 for v in [very_low, low, normal, high, very_high]):
                logger.warning(f"Photo {i}: Missing saturation distribution data (all zeros)")
                continue

            # Try to convert to float
            try:
                very_low_val = float(very_low)
                low_val = float(low)
                normal_val = float(normal)
                high_val = float(high)
                very_high_val = float(very_high)
            except (TypeError, ValueError) as e:
                logger.error(f"Photo {i}: Cannot convert saturation distribution data: {e}")
                continue

            # Add to arrays
            full_name = data.get('photo_name', f"Photo {i+1}")
            file_path = data.get('file_path', '')
            short_name = Path(full_name).stem[:15]
            photo_names.append(short_name)
            photo_paths.append(file_path)
            very_low_values.append(very_low_val)
            low_values.append(low_val)
            normal_values.append(normal_val)
            high_values.append(high_val)
            very_high_values.append(very_high_val)

        logger.info(f"Successfully extracted saturation data for {len(photo_names)} photos")

        if not photo_names:
            # No valid data
            error_label = QLabel("❌ No saturation distribution data available.\n\n"
                                "Please re-analyze photos to generate this data.")
            error_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)
            return

        # If we have too many photos, show only a sample
        max_photos_display = 50
        if len(photo_names) > max_photos_display:
            logger.info(f"Too many photos ({len(photo_names)}), sampling {max_photos_display}")
            indices = np.linspace(0, len(photo_names) - 1, max_photos_display, dtype=int)
            photo_names = [photo_names[i] for i in indices]
            photo_paths = [photo_paths[i] for i in indices]
            very_low_values = [very_low_values[i] for i in indices]
            low_values = [low_values[i] for i in indices]
            normal_values = [normal_values[i] for i in indices]
            high_values = [high_values[i] for i in indices]
            very_high_values = [very_high_values[i] for i in indices]

        # Adjust canvas size based on number of photos
        width = max(12, len(photo_names) * 0.3)
        canvas = MplCanvas(parent_tab, width=width, height=6, is_dark=self.is_dark)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        ax = canvas.axes

        # Create stacked bar chart with saturation-appropriate colors
        x = np.arange(len(photo_names))
        width_bar = 0.8

        # Define colors for each saturation range (grayscale to vibrant)
        bars_very_low = ax.bar(x, very_low_values, width_bar, label='Very Low (<15%)',
                               color='#D3D3D3', alpha=0.8)

        bars_low = ax.bar(x, low_values, width_bar, bottom=very_low_values,
                          label='Low (15-30%)', color='#B0C4DE', alpha=0.8)

        bottom_normal = [vl + l for vl, l in zip(very_low_values, low_values)]
        bars_normal = ax.bar(x, normal_values, width_bar, bottom=bottom_normal,
                             label='Normal (30-50%)', color='#87CEEB', alpha=0.8)

        bottom_high = [b + n for b, n in zip(bottom_normal, normal_values)]
        bars_high = ax.bar(x, high_values, width_bar, bottom=bottom_high,
                           label='High (50-70%)', color='#4682B4', alpha=0.8)

        bottom_very_high = [b + h for b, h in zip(bottom_high, high_values)]
        bars_very_high = ax.bar(x, very_high_values, width_bar, bottom=bottom_very_high,
                                label='Very High (>70%)', color='#191970', alpha=0.8)

        ax.set_xlabel('Photos', fontsize=12, weight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=12, weight='bold')
        ax.set_title(f'Saturation Distribution Comparison ({len(photo_names)} photos)',
                     fontsize=14, weight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(photo_names, rotation=60, ha='right', fontsize=8)
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_facecolor(self._get_plot_bg_color())
        ax.set_ylim(0, 105)

        # Add interactive hover tooltip with photo preview
        self._add_hover_tooltip(canvas, ax, x, photo_names, photo_paths,
                                bars_very_low, bars_low, bars_normal,
                                bars_high, bars_very_high)

        canvas.figure.tight_layout()

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

    def _export_report(self):
        """Export statistics report"""
        from PySide6.QtWidgets import QMessageBox, QFileDialog

        # Ask for save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Statistics Report",
            str(Path.home() / f"statistics_{self.album_name}.png"),
            "PNG Image (*.png);;PDF Document (*.pdf)"
        )

        if filename:
            try:
                # Create a combined figure with all charts
                fig = Figure(figsize=(16, 12), dpi=150, facecolor='white')

                # You can add export logic here
                QMessageBox.information(self, "Export", f"Report would be saved to:\n{filename}")
                logger.info(f"Exported statistics to: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{e}")
                logger.error(f"Export failed: {e}")


def main():
    """Test the statistics window"""
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Test data
    test_data = [
        {'hue_mean': 18.5, 'saturation_mean': 0.45, 'lightness_mean': 0.52,
         'lightness_low': 15.3, 'lightness_mid': 68.4, 'lightness_high': 16.3, 'photo_name': 'Photo1.jpg'},
        {'hue_mean': 19.2, 'saturation_mean': 0.48, 'lightness_mean': 0.55,
         'lightness_low': 12.1, 'lightness_mid': 71.2, 'lightness_high': 16.7, 'photo_name': 'Photo2.jpg'},
        {'hue_mean': 20.1, 'saturation_mean': 0.42, 'lightness_mean': 0.50,
         'lightness_low': 18.5, 'lightness_mid': 65.8, 'lightness_high': 15.7, 'photo_name': 'Photo3.jpg'},
        {'hue_mean': 17.8, 'saturation_mean': 0.46, 'lightness_mean': 0.53,
         'lightness_low': 14.2, 'lightness_mid': 69.5, 'lightness_high': 16.3, 'photo_name': 'Photo4.jpg'},
    ]

    window = CC_StatisticsWindow("Test Album", test_data)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

