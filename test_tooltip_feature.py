"""
Test the multi-dimensional tooltip feature in CC_StatisticsWindow
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestTooltip")

from CC_StatisticsWindow import CC_StatisticsWindow

def create_test_data():
    """Create comprehensive test data with all required fields"""
    test_data = []

    # Create 5 test photos with varying distributions
    photos = [
        {
            'photo_name': 'Portrait_1.jpg',
            'file_path': '',  # Empty path for testing
            'hue_mean': 18.5,
            'saturation_mean': 0.45,
            'lightness_mean': 0.52,
            # Hue distribution
            'hue_very_red': 5.0,
            'hue_red_orange': 25.0,
            'hue_normal': 50.0,
            'hue_yellow': 15.0,
            'hue_very_yellow': 3.0,
            'hue_abnormal': 2.0,
            # Saturation distribution
            'sat_very_low': 10.0,
            'sat_low': 15.0,
            'sat_normal': 45.0,
            'sat_high': 20.0,
            'sat_very_high': 10.0,
            # Lightness distribution
            'lightness_low': 15.3,
            'lightness_mid': 68.4,
            'lightness_high': 16.3,
        },
        {
            'photo_name': 'Portrait_2.jpg',
            'file_path': '',
            'hue_mean': 22.1,
            'saturation_mean': 0.52,
            'lightness_mean': 0.58,
            # Hue distribution
            'hue_very_red': 3.0,
            'hue_red_orange': 20.0,
            'hue_normal': 60.0,
            'hue_yellow': 12.0,
            'hue_very_yellow': 4.0,
            'hue_abnormal': 1.0,
            # Saturation distribution
            'sat_very_low': 8.0,
            'sat_low': 12.0,
            'sat_normal': 50.0,
            'sat_high': 22.0,
            'sat_very_high': 8.0,
            # Lightness distribution
            'lightness_low': 12.1,
            'lightness_mid': 71.2,
            'lightness_high': 16.7,
        },
        {
            'photo_name': 'Portrait_3.jpg',
            'file_path': '',
            'hue_mean': 25.8,
            'saturation_mean': 0.38,
            'lightness_mean': 0.48,
            # Hue distribution
            'hue_very_red': 8.0,
            'hue_red_orange': 18.0,
            'hue_normal': 55.0,
            'hue_yellow': 13.0,
            'hue_very_yellow': 5.0,
            'hue_abnormal': 1.0,
            # Saturation distribution
            'sat_very_low': 15.0,
            'sat_low': 20.0,
            'sat_normal': 40.0,
            'sat_high': 18.0,
            'sat_very_high': 7.0,
            # Lightness distribution
            'lightness_low': 18.5,
            'lightness_mid': 65.8,
            'lightness_high': 15.7,
        },
        {
            'photo_name': 'Portrait_4.jpg',
            'file_path': '',
            'hue_mean': 19.2,
            'saturation_mean': 0.48,
            'lightness_mean': 0.55,
            # Hue distribution
            'hue_very_red': 6.0,
            'hue_red_orange': 28.0,
            'hue_normal': 48.0,
            'hue_yellow': 14.0,
            'hue_very_yellow': 3.0,
            'hue_abnormal': 1.0,
            # Saturation distribution
            'sat_very_low': 9.0,
            'sat_low': 13.0,
            'sat_normal': 48.0,
            'sat_high': 21.0,
            'sat_very_high': 9.0,
            # Lightness distribution
            'lightness_low': 14.2,
            'lightness_mid': 69.5,
            'lightness_high': 16.3,
        },
        {
            'photo_name': 'Portrait_5.jpg',
            'file_path': '',
            'hue_mean': 21.5,
            'saturation_mean': 0.42,
            'lightness_mean': 0.51,
            # Hue distribution
            'hue_very_red': 4.0,
            'hue_red_orange': 22.0,
            'hue_normal': 58.0,
            'hue_yellow': 11.0,
            'hue_very_yellow': 4.0,
            'hue_abnormal': 1.0,
            # Saturation distribution
            'sat_very_low': 12.0,
            'sat_low': 18.0,
            'sat_normal': 42.0,
            'sat_high': 20.0,
            'sat_very_high': 8.0,
            # Lightness distribution
            'lightness_low': 16.8,
            'lightness_mid': 67.2,
            'lightness_high': 16.0,
        },
    ]

    return photos

def main():
    """Run the test"""
    logger.info("Starting tooltip feature test...")

    app = QApplication(sys.argv)

    # Create test data
    test_data = create_test_data()
    logger.info(f"Created {len(test_data)} test photos with full distribution data")

    # Create and show statistics window
    window = CC_StatisticsWindow("Test Album - Tooltip Feature", test_data)
    window.show()

    logger.info("Statistics window opened")
    logger.info("Instructions:")
    logger.info("1. Navigate to any of the comparison tabs: Hue, Saturation, or Lightness")
    logger.info("2. Hover over any bar in the chart")
    logger.info("3. You should see a COMPACT tooltip showing:")
    logger.info("   - Photo name (text)")
    logger.info("   - The OTHER TWO dimensions as mini horizontal bars (NO legends)")
    logger.info("4. The mini bars are the same width as main chart bars")
    logger.info("5. Just look at the color proportions - very intuitive!")
    logger.info("6. For details, switch to the corresponding comparison tab")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
