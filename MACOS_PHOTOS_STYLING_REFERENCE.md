# macOS Photos Gallery - Quick Styling Reference

## 🎨 Thumbnail Styles

### Container Frame
```python
CC_PhotoThumbnail {
    background-color: transparent;
    border: 4px solid transparent;  # No border by default
    border-radius: 12px;            # Rounded container
}
```

### Selected State
```python
CC_PhotoThumbnail {
    background-color: transparent;
    border: 4px solid #007AFF;      # macOS Accent Blue
    border-radius: 12px;
}
```

### Hover State
```python
CC_PhotoThumbnail:hover {
    background-color: rgba(0, 0, 0, 0.02);  # Subtle dark overlay
}
```

### Thumbnail Label
```python
QLabel {
    background-color: #f5f5f5;      # Light gray placeholder
    border-radius: 10px;             # Rounded corners
}
```

## 🎚️ Zoom Slider Styles

### Groove (Track)
```python
QSlider::groove:horizontal {
    border: 1px solid #bbb;
    background: #f0f0f0;
    height: 4px;
    border-radius: 2px;
}
```

### Handle (Thumb)
```python
QSlider::handle:horizontal {
    background: #007AFF;            # macOS Blue
    border: 1px solid #006FE8;      # Darker blue border
    width: 14px;
    margin: -6px 0;                 # Center vertically
    border-radius: 7px;             # Circular handle
}
```

### Handle Hover
```python
QSlider::handle:horizontal:hover {
    background: #0062D1;            # Darker on hover
}
```

## 📐 Layout Specifications

| Property | Value | Notes |
|----------|-------|-------|
| Grid Spacing | 6px | Dense, organized layout |
| Thumbnail Min | 120px | Smallest zoom level |
| Thumbnail Default | 200px | Standard size |
| Thumbnail Max | 300px | Largest zoom level |
| Border Width | 4px | Selection indicator |
| Border Radius (Container) | 12px | Outer rounded corners |
| Border Radius (Image) | 10px | Inner rounded corners |
| Container Margins | 0px | Edge-to-edge content |

## 🎯 Color Palette

| Color Name | Hex | Usage |
|------------|-----|-------|
| macOS Accent Blue | `#007AFF` | Selection border, slider |
| Darker Blue | `#006FE8` | Slider border |
| Hover Blue | `#0062D1` | Slider hover |
| Placeholder Gray | `#f5f5f5` | Loading background |
| Border Gray | `#bbb` | Slider track border |
| Track Gray | `#f0f0f0` | Slider track background |
| Hover Overlay | `rgba(0, 0, 0, 0.02)` | Subtle hover effect |

## 🔢 Column Count Logic

```python
if thumbnail_size <= 150:
    columns = 5  # Small thumbnails
elif thumbnail_size <= 200:
    columns = 4  # Medium thumbnails
else:
    columns = 3  # Large thumbnails
```

## 📱 Responsive Behavior

- **Zoom Slider Change**: Triggers full grid reload with new thumbnail size
- **Selection**: Previous selection cleared automatically (single selection mode)
- **Hover**: Subtle feedback without layout shift
- **Border**: Uses transparent border when not selected to avoid layout shift

## 🚀 Performance Notes

- Virtual scrolling remains intact
- Thumbnails load on-demand
- Database cache adapts to current zoom level
- Selection state managed at widget level (no DOM-style queries)

---

**Implementation Status:** ✅ Complete  
**Date:** February 14, 2026  
**Platform:** Windows/macOS/Linux (PySide6)

