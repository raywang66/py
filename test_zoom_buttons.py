"""
Test script for new zoom button functionality
"""

def test_zoom_levels():
    """Test zoom level logic"""
    zoom_levels = [9, 7, 5, 3]  # Column counts

    print("=== Testing Zoom Level System ===\n")

    # Test all levels
    for i, cols in enumerate(zoom_levels):
        print(f"Level {i}: {cols} columns")
        print(f"  + button enabled: {i > 0}")
        print(f"  - button enabled: {i < len(zoom_levels) - 1}")

    print("\n=== Testing Zoom In (+ button) ===")
    current_level = 2  # Start at default (5 cols)
    print(f"Starting at level {current_level} ({zoom_levels[current_level]} cols)")

    # Zoom in twice
    for step in range(1, 3):
        if current_level > 0:
            current_level -= 1
            print(f"Step {step}: Zoomed in to level {current_level} ({zoom_levels[current_level]} cols)")
        else:
            print(f"Step {step}: Cannot zoom in further (at minimum)")

    print("\n=== Testing Zoom Out (- button) ===")
    current_level = 2  # Reset to default
    print(f"Starting at level {current_level} ({zoom_levels[current_level]} cols)")

    # Zoom out twice
    for step in range(1, 3):
        if current_level < len(zoom_levels) - 1:
            current_level += 1
            print(f"Step {step}: Zoomed out to level {current_level} ({zoom_levels[current_level]} cols)")
        else:
            print(f"Step {step}: Cannot zoom out further (at maximum)")

    print("\n=== Testing Responsive Sizing ===")
    window_widths = [1920, 1440, 1024, 800]
    spacing = 3

    for width in window_widths:
        for level, cols in enumerate(zoom_levels):
            # Calculate thumbnail size
            available = width - 20  # Subtract margins
            thumbnail_size = (available - spacing * (cols + 1)) / cols
            thumbnail_size = max(100, int(thumbnail_size))  # Min 100px

            print(f"Window {width}px, Level {level} ({cols} cols): "
                  f"thumbnail = {thumbnail_size}px")

def test_settings():
    """Test settings persistence"""
    print("\n\n=== Testing Settings Persistence ===\n")

    try:
        from CC_Settings import CC_Settings

        # Create settings instance
        settings = CC_Settings()

        # Test get default
        default_level = settings.get_zoom_level_index()
        print(f"Default zoom level index: {default_level}")

        # Test set and get
        test_levels = [0, 1, 2, 3]
        for level in test_levels:
            settings.set_zoom_level_index(level)
            retrieved = settings.get_zoom_level_index()
            status = "✓" if retrieved == level else "✗"
            print(f"{status} Set level {level}, got {retrieved}")

        # Reset to default
        settings.set_zoom_level_index(2)
        settings.save()
        print("\nReset to default level 2 and saved")

    except Exception as e:
        print(f"Error testing settings: {e}")

if __name__ == "__main__":
    test_zoom_levels()
    test_settings()
    print("\n=== All Tests Complete ===")

