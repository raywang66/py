"""
ChromaCloud Settings Manager
Saves and restores application state between sessions
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CC_Settings:
    """Manages application settings persistence"""

    def __init__(self, settings_file: str = "chromacloud_settings.json"):
        """Initialize settings manager

        Args:
            settings_file: Name of settings file (stored in app directory)
        """
        self.settings_file = Path(__file__).parent / settings_file
        self.settings: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                logger.info(f"✅ Loaded settings from {self.settings_file}")
            else:
                logger.info("No existing settings file, using defaults")
                self.settings = self._get_defaults()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.settings = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'window': {
                'x': 100,
                'y': 100,
                'width': 1400,
                'height': 900,
                'maximized': False
            },
            'ui': {
                'dark_mode': False,
                'zoom_level': 200  # Default thumbnail size
            },
            'navigation': {
                'last_album_id': None,
                'last_folder_path': None,
                'selected_item_type': None  # 'album', 'folder', or 'all_photos'
            }
        }

    def save(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved settings to {self.settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    # Window settings
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window position and size"""
        return self.settings.get('window', self._get_defaults()['window'])

    def set_window_geometry(self, x: int, y: int, width: int, height: int, maximized: bool = False):
        """Save window position and size"""
        self.settings['window'] = {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'maximized': maximized
        }

    # UI settings
    def get_dark_mode(self) -> bool:
        """Get dark mode preference"""
        return self.settings.get('ui', {}).get('dark_mode', False)

    def set_dark_mode(self, enabled: bool):
        """Save dark mode preference"""
        if 'ui' not in self.settings:
            self.settings['ui'] = {}
        self.settings['ui']['dark_mode'] = enabled

    def get_zoom_level(self) -> int:
        """Get zoom level (thumbnail size)"""
        return self.settings.get('ui', {}).get('zoom_level', 200)

    def set_zoom_level(self, zoom: int):
        """Save zoom level"""
        if 'ui' not in self.settings:
            self.settings['ui'] = {}
        self.settings['ui']['zoom_level'] = zoom

    # Navigation settings
    def get_last_album_id(self) -> Optional[int]:
        """Get last viewed album ID"""
        return self.settings.get('navigation', {}).get('last_album_id')

    def set_last_album_id(self, album_id: Optional[int]):
        """Save last viewed album ID"""
        if 'navigation' not in self.settings:
            self.settings['navigation'] = {}
        self.settings['navigation']['last_album_id'] = album_id

    def get_last_folder_path(self) -> Optional[str]:
        """Get last viewed folder path"""
        return self.settings.get('navigation', {}).get('last_folder_path')

    def set_last_folder_path(self, path: Optional[str]):
        """Save last viewed folder path"""
        if 'navigation' not in self.settings:
            self.settings['navigation'] = {}
        self.settings['navigation']['last_folder_path'] = path

    def get_selected_item_type(self) -> Optional[str]:
        """Get last selected item type ('album', 'folder', 'all_photos')"""
        return self.settings.get('navigation', {}).get('selected_item_type')

    def set_selected_item_type(self, item_type: Optional[str]):
        """Save last selected item type"""
        if 'navigation' not in self.settings:
            self.settings['navigation'] = {}
        self.settings['navigation']['selected_item_type'] = item_type

