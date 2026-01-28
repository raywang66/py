# ChromaCloud (CC) - High-Level Architecture

## 📐 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CC_MainApp (PySide6)                       │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  CC_UIManager │  │ CC_DBManager │  │ CC_PhotoLibrary  │    │
│  │  (macOS UI)   │  │  (SQLite)    │  │  (Albums/Proj)   │    │
│  └───────┬───────┘  └──────┬───────┘  └────────┬─────────┘    │
│          │                  │                    │              │
│          └──────────────────┴────────────────────┘              │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│                    CC_ComputeEngine                             │
│  ┌─────────────────────┐    ┌──────────────────────────┐      │
│  │  CC_SkinProcessor   │───▶│  CC_Renderer3D           │      │
│  │  (PyTorch GPU)      │    │  (Taichi Lang)           │      │
│  │  - Face Parsing     │    │  - HSL Point Cloud       │      │
│  │  - Skin Masking     │    │  - Dual-View Comparison  │      │
│  │  - HSL Conversion   │    │  - Metal/Vulkan/DX12     │      │
│  └─────────────────────┘    └──────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Core Modules

### 1. CC_MainApp
- **Role**: Application entry point and coordinator
- **Tech**: PySide6 (Qt6) with native window effects
- **Responsibilities**:
  - Window management (Mica/Acrylic effects)
  - Route events between UI and compute modules
  - Session state management

### 2. CC_UIManager
- **Role**: macOS-inspired UI components
- **Components**:
  - `CC_SidebarNav`: Albums/Projects navigation
  - `CC_PhotoGrid`: Fluid responsive photo grid
  - `CC_DualViewPanel`: Side-by-side comparison view
  - `CC_3DViewport`: Embedded Taichi rendering canvas
- **Style**: Minimalist, translucent panels, smooth animations

### 3. CC_DBManager
- **Role**: Photo metadata and project persistence
- **Schema**:
  ```sql
  photos (id, path, hash, import_date, metadata_json)
  albums (id, name, created_at, cover_photo_id)
  projects (id, name, description, config_json)
  album_photos (album_id, photo_id, order)
  project_photos (project_id, photo_id, analysis_cache)
  ```

### 4. CC_SkinProcessor (PyTorch)
- **Role**: AI-powered skin segmentation and color extraction
- **Pipeline**:
  1. **Face Detection**: Detect face bounding box
  2. **Face Parsing**: Segment with BiSeNet/FaceParser model
  3. **Skin Masking**: Extract skin pixels (exclude eyes, lips, brows, beard)
  4. **RGB → HSL**: Convert masked pixels to HSL color space
  5. **Filter by Hue**: Keep only H ∈ [15°, 25°] (skin tone range)
  6. **Output**: Nx3 tensor (H, S, L coordinates)
- **Optimization**: Batch processing, FP16 inference, CUDA streams

### 5. CC_Renderer3D (Taichi)
- **Role**: Real-time 3D point cloud visualization
- **Features**:
  - Render HSL cylindrical wedge (H: 15°-25°)
  - Interactive camera (orbit, zoom, pan)
  - Dual-photo overlay (different colors)
  - GPU-accelerated rasterization
- **Platform Detection**:
  - macOS → `ti.metal`
  - Windows → `ti.vulkan` or `ti.dx12`

### 6. CC_PhotoLibrary
- **Role**: Photo import, indexing, and album management
- **Features**:
  - RAW file support (ARW, CR2, NEF via rawpy)
  - JPEG/PNG support
  - Smart albums (e.g., "Recently Added", "Skin Analyzed")
  - Project-based workflows (group photos for batch analysis)

## 🔄 Data Flow

### Single Photo Analysis
```
User Selects Photo
    ↓
CC_PhotoLibrary loads image → CC_SkinProcessor
    ↓
Face Parsing (PyTorch CUDA)
    ↓
Skin Mask Generation (exclude non-skin)
    ↓
RGB → HSL conversion
    ↓
Filter H ∈ [15°, 25°]
    ↓
CC_Renderer3D receives Nx3 point cloud
    ↓
Taichi renders 3D HSL wedge in CC_3DViewport
```

### Dual-View Comparison
```
User Selects Photo A & Photo B
    ↓
CC_SkinProcessor processes both in parallel
    ↓
Point Cloud A (color: #FF6B6B - Red)
Point Cloud B (color: #4ECDC4 - Cyan)
    ↓
CC_Renderer3D overlays both clouds
    ↓
User sees "shift" in 3D space (e.g., White vs. Golden skin tone)
```

## 🛠️ Technical Decisions

### Why PySide6?
- Native Qt performance
- Excellent cross-platform support
- Built-in OpenGL/Metal/Vulkan integration
- Commercial-friendly license

### Why Taichi Lang?
- Python-native GPU programming
- Automatic backend selection (Metal/Vulkan/CUDA/DX12)
- 10-100x faster than NumPy for graphics kernels
- Clean syntax for 3D rendering pipelines

### Why PyTorch for Segmentation?
- Industry-standard for CV models
- Excellent CUDA/Metal support
- Pre-trained face parsing models available
- Easy model deployment (TorchScript)

## 📦 Project Structure

```
ChromaCloud/
├── cc_main.py                 # Application entry point
├── cc_config.py               # Global configuration
├── requirements_cc.txt        # Dependencies
│
├── core/
│   ├── CC_MainApp.py          # Main application coordinator
│   ├── CC_ComputeEngine.py    # Compute orchestration
│   ├── CC_SkinProcessor.py    # PyTorch segmentation pipeline
│   ├── CC_Renderer3D.py       # Taichi 3D rendering
│   ├── CC_DBManager.py        # SQLite database layer
│   └── CC_PhotoLibrary.py     # Photo management
│
├── ui/
│   ├── CC_UIManager.py        # UI coordinator
│   ├── CC_SidebarNav.py       # Navigation sidebar
│   ├── CC_PhotoGrid.py        # Photo grid view
│   ├── CC_DualViewPanel.py    # Comparison panel
│   ├── CC_3DViewport.py       # 3D viewport widget
│   └── styles/
│       ├── cc_macos_style.qss # macOS-inspired stylesheet
│       └── cc_dark_theme.qss  # Dark theme
│
├── models/
│   ├── face_parsing_bisenet.pth  # Pre-trained model
│   └── model_loader.py            # Model management
│
└── utils/
    ├── CC_ColorSpace.py       # RGB/HSL conversion utilities
    ├── CC_ImageIO.py          # RAW/JPEG/PNG loading
    └── CC_PlatformDetect.py   # OS detection for GPU backend
```

## 🚀 Performance Targets

| Metric | Target | Hardware |
|--------|--------|----------|
| Face Parsing Inference | < 50ms | RTX 3050 Ti |
| HSL Conversion (1000x1000 px) | < 10ms | CUDA |
| Point Cloud Rendering (60K points) | 60 FPS | Taichi Metal/Vulkan |
| Photo Grid Scrolling | 120 FPS | Qt QML |
| Album Load Time (1000 photos) | < 200ms | SQLite indexed |

## 🔐 Archiving Standard

All classes, functions, and files follow the **CC_** prefix convention:
- Classes: `CC_ClassName`
- Functions: `CC_function_name()` (if global utility)
- Files: `CC_ModuleName.py`
- Constants: `CC_CONSTANT_NAME`

This ensures zero namespace conflicts and clear project ownership.

