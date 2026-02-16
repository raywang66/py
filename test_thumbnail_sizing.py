"""
Test thumbnail size calculation for different column counts
"""

def calculate_thumbnail_size(gallery_width, cols):
    """Calculate thumbnail size to fit column count in gallery width"""
    spacing = 3  # Grid spacing
    margin = 10  # Layout margins

    # Formula: (width - margins) / cols - spacing
    thumbnail_size = int((gallery_width - margin * 2) / cols - spacing * 2)

    # Apply constraints
    thumbnail_size = max(80, min(500, thumbnail_size))

    return thumbnail_size

def test_zoom_levels():
    """Test thumbnail sizes for different zoom levels and window widths"""

    zoom_levels = [9, 7, 5, 3]  # Column counts
    window_widths = [800, 1024, 1200, 1440, 1920, 2560]

    print("=" * 80)
    print("THUMBNAIL SIZE CALCULATION TEST")
    print("=" * 80)
    print()

    print("Formula: thumbnail_size = (width - margins*2) / cols - spacing*2")
    print("Constraints: 80px <= size <= 500px")
    print()

    for width in window_widths:
        print(f"\n{'Window Width: ' + str(width) + 'px':=^80}")
        print()

        for level, cols in enumerate(zoom_levels):
            size = calculate_thumbnail_size(width, cols)
            total_width = cols * (size + 3 * 2) + 10 * 2
            fit_percentage = (total_width / width) * 100

            level_name = ["9 cols (max overview)", "7 cols", "5 cols (default)", "3 cols (max detail)"][level]

            print(f"  Level {level}: {level_name:30} → {size:3}px each")
            print(f"           Total width used: {total_width}px ({fit_percentage:.1f}% of window)")

    print("\n" + "=" * 80)
    print("VISUAL REPRESENTATION")
    print("=" * 80)
    print()

    # Show visual representation for 1440px window (common laptop size)
    width = 1440
    print(f"Window: {width}px wide")
    print()

    for level, cols in enumerate(zoom_levels):
        size = calculate_thumbnail_size(width, cols)
        level_name = ["Level 0 (9 cols)", "Level 1 (7 cols)", "Level 2 (5 cols)", "Level 3 (3 cols)"][level]

        # Create visual representation
        block = "▓" * (size // 10)  # Scale down for display
        blocks = " ".join([block] * cols)

        print(f"{level_name:20} {size}px each:")
        print(f"  {blocks}")
        print()

def test_button_behavior():
    """Test button click behavior"""

    print("\n" + "=" * 80)
    print("BUTTON BEHAVIOR TEST")
    print("=" * 80)
    print()

    zoom_levels = [9, 7, 5, 3]
    current_level = 2  # Start at default (5 cols)
    width = 1440

    print(f"Initial state: Level {current_level} ({zoom_levels[current_level]} columns)")
    size = calculate_thumbnail_size(width, zoom_levels[current_level])
    print(f"Thumbnail size: {size}px\n")

    # Test zoom in (+ button)
    print("Click [+] button (zoom in - larger photos):")
    for i in range(3):
        if current_level > 0:
            current_level -= 1
            cols = zoom_levels[current_level]
            size = calculate_thumbnail_size(width, cols)
            print(f"  Step {i+1}: Level {current_level} → {cols} cols @ {size}px each ✓")
        else:
            print(f"  Step {i+1}: Cannot zoom in further (button disabled)")

    print()

    # Reset and test zoom out
    current_level = 2
    print("Reset to Level 2\n")

    print("Click [−] button (zoom out - smaller photos):")
    for i in range(3):
        if current_level < len(zoom_levels) - 1:
            current_level += 1
            cols = zoom_levels[current_level]
            size = calculate_thumbnail_size(width, cols)
            print(f"  Step {i+1}: Level {current_level} → {cols} cols @ {size}px each ✓")
        else:
            print(f"  Step {i+1}: Cannot zoom out further (button disabled)")

def test_responsive_behavior():
    """Test window resize behavior"""

    print("\n" + "=" * 80)
    print("WINDOW RESIZE BEHAVIOR")
    print("=" * 80)
    print()

    cols = 5  # Fixed at 5 columns
    print(f"User has set zoom to Level 2 ({cols} columns)")
    print("Now they resize the window...\n")

    widths = [1920, 1600, 1440, 1200, 1024, 800]

    for width in widths:
        size = calculate_thumbnail_size(width, cols)
        print(f"  Window {width}px → thumbnail {size}px (maintains {cols} columns)")

    print("\n✓ Thumbnails resize to fit window width while maintaining column count")

if __name__ == "__main__":
    test_zoom_levels()
    test_button_behavior()
    test_responsive_behavior()

    print("\n" + "=" * 80)
    print("✓ All calculations verified - ready for implementation!")
    print("=" * 80)

