"""
Test script for the new Hue Distribution Comparison feature
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from CC_StatisticsWindow import CC_StatisticsWindow

# Test data with hue distribution
test_data = [
    {
        'hue_mean': 18.5,
        'saturation_mean': 0.45,
        'lightness_mean': 0.52,
        'lightness_low': 15.3,
        'lightness_mid': 68.4,
        'lightness_high': 16.3,
        'hue_very_red': 5.2,
        'hue_red_orange': 25.8,
        'hue_normal': 55.3,
        'hue_yellow': 10.2,
        'hue_very_yellow': 2.5,
        'hue_abnormal': 1.0,
        'photo_name': 'Photo1.jpg',
        'file_path': str(Path(__file__).parent / 'Photos' / 'Photo1.jpg')
    },
    {
        'hue_mean': 22.3,
        'saturation_mean': 0.48,
        'lightness_mean': 0.55,
        'lightness_low': 12.1,
        'lightness_mid': 71.2,
        'lightness_high': 16.7,
        'hue_very_red': 2.1,
        'hue_red_orange': 15.5,
        'hue_normal': 68.2,
        'hue_yellow': 12.1,
        'hue_very_yellow': 1.8,
        'hue_abnormal': 0.3,
        'photo_name': 'Photo2.jpg',
        'file_path': str(Path(__file__).parent / 'Photos' / 'Photo2.jpg')
    },
    {
        'hue_mean': 28.1,
        'saturation_mean': 0.42,
        'lightness_mean': 0.50,
        'lightness_low': 18.5,
        'lightness_mid': 65.8,
        'lightness_high': 15.7,
        'hue_very_red': 1.2,
        'hue_red_orange': 8.5,
        'hue_normal': 45.3,
        'hue_yellow': 35.2,
        'hue_very_yellow': 8.5,
        'hue_abnormal': 1.3,
        'photo_name': 'Photo3.jpg',
        'file_path': str(Path(__file__).parent / 'Photos' / 'Photo3.jpg')
    },
    {
        'hue_mean': 15.8,
        'saturation_mean': 0.46,
        'lightness_mean': 0.53,
        'lightness_low': 14.2,
        'lightness_mid': 69.5,
        'lightness_high': 16.3,
        'hue_very_red': 8.5,
        'hue_red_orange': 35.2,
        'hue_normal': 48.3,
        'hue_yellow': 6.5,
        'hue_very_yellow': 1.2,
        'hue_abnormal': 0.3,
        'photo_name': 'Photo4.jpg',
        'file_path': str(Path(__file__).parent / 'Photos' / 'Photo4.jpg')
    },
    {
        'hue_mean': 33.2,
        'saturation_mean': 0.52,
        'lightness_mean': 0.48,
        'lightness_low': 20.1,
        'lightness_mid': 62.3,
        'lightness_high': 17.6,
        'hue_very_red': 0.5,
        'hue_red_orange': 5.2,
        'hue_normal': 28.5,
        'hue_yellow': 48.3,
        'hue_very_yellow': 15.5,
        'hue_abnormal': 2.0,
        'photo_name': 'Photo5.jpg',
        'file_path': str(Path(__file__).parent / 'Photos' / 'Photo5.jpg')
    }
]


def main():
    app = QApplication(sys.argv)

    window = CC_StatisticsWindow("Test Album - Hue Distribution", test_data)
    window.show()

    print("✅ Statistics window opened successfully!")
    print("📊 Check the '🌈 Hue Comparison' tab to see the new feature")
    print("🎨 Hue distribution ranges:")
    print("   - Very Red (0-10°, 350-360°): Dark red")
    print("   - Red-Orange (10-20°): Light red")
    print("   - Normal (20-30°): Tan/beige")
    print("   - Yellow (30-40°): Golden")
    print("   - Very Yellow (40-60°): Bright yellow")
    print("   - Abnormal (60-350°): Gray")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
