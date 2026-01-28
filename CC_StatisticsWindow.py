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
    QTabWidget, QScrollArea, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

logger = logging.getLogger("CC_Statistics")


class MplCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for embedding in Qt"""

    def __init__(self, parent=None, width=8, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)


class CC_StatisticsWindow(QWidget):
    """Advanced statistics window with multiple visualizations"""

    def __init__(self, album_name: str, stats_data: List[Dict]):
        super().__init__()
        self.album_name = album_name
        self.stats_data = stats_data

        self.setWindowTitle(f"Statistics - {album_name}")
        self.setGeometry(100, 100, 1400, 900)

        # Apply clean white theme
        self._apply_theme()
        self._create_ui()
        self._plot_all_charts()

        logger.info(f"Statistics window created for album: {album_name}")

    def _apply_theme(self):
        """Apply clean white theme (macOS Photos style)"""
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

        # Tab 1: Overview
        self.overview_tab = self._create_overview_tab()
        self.tabs.addTab(self.overview_tab, "📈 Overview")

        # Tab 2: Hue Analysis
        self.hue_tab = self._create_chart_tab()
        self.tabs.addTab(self.hue_tab, "🎨 Hue Distribution")

        # Tab 3: 3D Scatter
        self.scatter_tab = self._create_chart_tab()
        self.tabs.addTab(self.scatter_tab, "📊 HSL Scatter")

        # Tab 4: Lightness Distribution
        self.lightness_tab = self._create_chart_tab()
        self.tabs.addTab(self.lightness_tab, "💡 Lightness Analysis")

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

        # Plot 2: 3D HSL Scatter
        self._plot_3d_scatter(self.scatter_tab, hues, sats, lights, photo_names)

        # Plot 3: Lightness Distribution
        self._plot_lightness_distribution(self.lightness_tab)

    def _plot_hue_distribution(self, parent_tab: QWidget, hues: List[float]):
        """Plot hue distribution histogram"""
        layout = parent_tab.layout()

        canvas = MplCanvas(parent_tab, width=10, height=6)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        # Plot histogram
        ax = canvas.axes
        ax.hist(hues, bins=20, color='#007AFF', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Hue (degrees)', fontsize=12, weight='bold')
        ax.set_ylabel('Number of Photos', fontsize=12, weight='bold')
        ax.set_title('Hue Distribution Across Album', fontsize=14, weight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('#FAFAFA')

        # Add statistics annotations
        mean_hue = np.mean(hues)
        median_hue = np.median(hues)
        ax.axvline(mean_hue, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_hue:.1f}°')
        ax.axvline(median_hue, color='green', linestyle='--', linewidth=2, label=f'Median: {median_hue:.1f}°')
        ax.legend(fontsize=10)

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
        ax.set_facecolor('#FAFAFA')

        canvas.figure.tight_layout()

        layout.addWidget(toolbar)
        layout.addWidget(canvas)

    def _plot_lightness_distribution(self, parent_tab: QWidget):
        """Plot lightness distribution comparison"""
        layout = parent_tab.layout()

        canvas = MplCanvas(parent_tab, width=12, height=6)
        toolbar = NavigationToolbar2QT(canvas, parent_tab)

        ax = canvas.axes

        # Extract lightness distribution data if available
        photo_names = []
        low_values = []
        mid_values = []
        high_values = []

        for i, data in enumerate(self.stats_data):
            photo_names.append(data.get('photo_name', f"Photo {i+1}"))
            low_values.append(data.get('lightness_low', 33.3))
            mid_values.append(data.get('lightness_mid', 33.3))
            high_values.append(data.get('lightness_high', 33.3))

        # Create stacked bar chart
        x = np.arange(len(photo_names))
        width = 0.8

        ax.bar(x, low_values, width, label='Low (<33%)', color='#8B4513', alpha=0.8)
        ax.bar(x, mid_values, width, bottom=low_values, label='Mid (33-67%)', color='#CD853F', alpha=0.8)

        # Calculate bottom for high values
        bottom_high = [l + m for l, m in zip(low_values, mid_values)]
        ax.bar(x, high_values, width, bottom=bottom_high, label='High (>67%)', color='#F4A460', alpha=0.8)

        ax.set_xlabel('Photos', fontsize=12, weight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=12, weight='bold')
        ax.set_title('Lightness Distribution Comparison', fontsize=14, weight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(photo_names, rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax.set_facecolor('#FAFAFA')
        ax.set_ylim(0, 100)

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

