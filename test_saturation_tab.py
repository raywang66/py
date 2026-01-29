"""
Quick test to verify CC_StatisticsWindow has saturation_comparison_tab
"""
import sys
from pathlib import Path

# Test data
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
        'sat_very_low': 8.5,
        'sat_low': 22.3,
        'sat_normal': 58.2,
        'sat_high': 9.5,
        'sat_very_high': 1.5,
        'photo_name': 'Photo1.jpg',
        'file_path': str(Path(__file__).parent / 'Photos' / 'Photo1.jpg')
    }
]

print("Testing CC_StatisticsWindow import...")
try:
    from CC_StatisticsWindow import CC_StatisticsWindow
    print("✅ Import successful")

    print("\nCreating window instance...")
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    window = CC_StatisticsWindow("Test Album", test_data)

    # Check if saturation_comparison_tab exists
    if hasattr(window, 'saturation_comparison_tab'):
        print("✅ saturation_comparison_tab exists")
    else:
        print("❌ saturation_comparison_tab NOT FOUND")
        print(f"Available attributes: {[a for a in dir(window) if 'tab' in a]}")

    # Check all tabs
    tab_count = window.tabs.count()
    print(f"\n📊 Total tabs: {tab_count}")
    for i in range(tab_count):
        print(f"  Tab {i}: {window.tabs.tabText(i)}")

    print("\n✅ Test completed successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
