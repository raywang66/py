"""
Test script to verify platform-specific data directory configuration
"""

import platform
from pathlib import Path

def get_data_directory():
    """Get platform-specific data directory for ChromaCloud files"""
    os_type = platform.system()

    if os_type == "Darwin":  # macOS
        # Use ~/CC for data files when running on macOS (SMB share friendly)
        data_dir = Path.home() / "CC"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    else:
        # Windows/Linux: use script directory
        return Path(__file__).parent

# Get data directory
DATA_DIR = get_data_directory()
LOG_FILE = DATA_DIR / "chromacloud.log"
DB_FILE = DATA_DIR / "chromacloud.db"

print("=" * 70)
print("ChromaCloud - Data Directory Test")
print("=" * 70)
print(f"Operating System: {platform.system()}")
print(f"Platform: {platform.platform()}")
print(f"Home Directory: {Path.home()}")
print()
print(f"Data Directory: {DATA_DIR}")
print(f"Database Path: {DB_FILE}")
print(f"Log File Path: {LOG_FILE}")
print()
print(f"Data directory exists: {DATA_DIR.exists()}")
print(f"Data directory is absolute: {DATA_DIR.is_absolute()}")
print("=" * 70)
