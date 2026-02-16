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

                # Migrate old dark_mode to new appearance_mode
                if 'ui' in self.settings and 'dark_mode' in self.settings['ui']:
                    dark_mode = self.settings['ui'].pop('dark_mode')
                    if 'appearance_mode' not in self.settings['ui']:
                        # Convert: dark_mode=True -> 'dark', dark_mode=False -> 'light'
                        self.settings['ui']['appearance_mode'] = 'dark' if dark_mode else 'light'
                        logger.info(f"🔄 Migrated dark_mode={dark_mode} to appearance_mode={self.settings['ui']['appearance_mode']}")
                        self.save()  # Save migrated settings
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
                'appearance_mode': 'system',  # 'system', 'light', 'dark'
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
    def get_appearance_mode(self) -> str:
        """Get appearance mode: 'system', 'light', or 'dark'"""
        return self.settings.get('ui', {}).get('appearance_mode', 'system')

    def set_appearance_mode(self, mode: str):
        """Set appearance mode: 'system', 'light', or 'dark'"""
        if 'ui' not in self.settings:
            self.settings['ui'] = {}
        self.settings['ui']['appearance_mode'] = mode

    def get_zoom_level(self) -> int:
        """Get zoom level (thumbnail size) - deprecated, kept for compatibility"""
        return self.settings.get('ui', {}).get('zoom_level', 200)

    def set_zoom_level(self, zoom: int):
        """Save zoom level - deprecated, kept for compatibility"""
        if 'ui' not in self.settings:
            self.settings['ui'] = {}
        self.settings['ui']['zoom_level'] = zoom

    def get_zoom_level_index(self) -> int:
        """Get zoom level index (0-3) for 4-level zoom: 3,5,7,9 columns"""
        return self.settings.get('ui', {}).get('zoom_level_index', 1)  # Default to level 1 (5 cols)

    def set_zoom_level_index(self, index: int):
        """Save zoom level index (0-3)"""
        if 'ui' not in self.settings:
            self.settings['ui'] = {}
        self.settings['ui']['zoom_level_index'] = index

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

