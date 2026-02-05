"""
ChromaCloud (CC) - Folder Watcher Module
Author: Senior Software Architect
Date: February 2026

Monitors folders for new photos and triggers automatic analysis.
Similar to Obsidian's vault monitoring.
"""

import logging
from pathlib import Path
from typing import Set, Optional, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from PySide6.QtCore import QThread, Signal
import time

logger = logging.getLogger("CC_FolderWatcher")


class CC_FolderWatcher(QThread):
    """文件夹监控线程，自动发现新照片"""

    # 信号
    new_photos_found = Signal(list)  # 发现新照片 [Path, ...]
    photos_removed = Signal(list)    # 照片被删除 [Path, ...]
    photos_modified = Signal(list)   # 照片被修改 [Path, ...]
    scan_progress = Signal(int, str) # 扫描进度 (percentage, message)
    scan_complete = Signal(int)      # 扫描完成 (photo_count)
    error = Signal(str)              # 错误信息

    def __init__(self, folder_path: Path, album_id: int):
        super().__init__()
        self.folder_path = folder_path
        self.album_id = album_id
        self.observer: Optional[Observer] = None
        self.known_photos: Set[Path] = set()
        self.running = True

        # 支持的图片格式
        self.image_extensions = {
            '.jpg', '.jpeg', '.png',
            '.arw', '.nef', '.cr2', '.cr3', '.dng',  # RAW formats
            '.JPG', '.JPEG', '.PNG',
            '.ARW', '.NEF', '.CR2', '.CR3', '.DNG'
        }

    def initial_scan(self) -> list:
        """初始扫描：发现所有现有照片"""
        try:
            logger.info(f"[FolderWatcher] Starting initial scan: {self.folder_path}")
            all_photos = []

            # 递归查找所有图片文件
            total_files = sum(1 for _ in self.folder_path.rglob('*') if _.is_file())
            processed = 0

            for file_path in self.folder_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in self.image_extensions:
                    all_photos.append(file_path)

                processed += 1
                if processed % 100 == 0:
                    progress = int((processed / max(total_files, 1)) * 100)
                    self.scan_progress.emit(progress, f"Scanning: {file_path.name}")

            self.known_photos = set(all_photos)
            logger.info(f"[FolderWatcher] Found {len(all_photos)} photos in {self.folder_path}")
            self.scan_complete.emit(len(all_photos))

            return all_photos

        except PermissionError as e:
            error_msg = f"Permission denied: {self.folder_path}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            return []
        except Exception as e:
            error_msg = f"Scan error: {e}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
            return []

    def start_watching(self):
        """开始监控文件系统"""
        try:
            if not self.folder_path.exists():
                error_msg = f"Folder does not exist: {self.folder_path}"
                logger.error(error_msg)
                self.error.emit(error_msg)
                return

            event_handler = FolderEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.folder_path), recursive=True)
            self.observer.start()
            logger.info(f"[FolderWatcher] Started monitoring: {self.folder_path}")

        except Exception as e:
            error_msg = f"Failed to start watching: {e}"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)

    def stop_watching(self):
        """停止监控"""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info(f"[FolderWatcher] Stopped monitoring: {self.folder_path}")

    def is_image(self, path: Path) -> bool:
        """检查文件是否为图片"""
        return path.suffix in self.image_extensions

    def run(self):
        """线程运行方法"""
        # 先等待一小段时间确保信号连接完成
        self.msleep(100)

        # 初始扫描
        all_photos = self.initial_scan()

        # 发送初始扫描的照片列表
        if all_photos and len(all_photos) > 0:
            logger.info(f"[FolderWatcher] Emitting {len(all_photos)} photos from initial scan")
            self.new_photos_found.emit(all_photos)

            # 等待确保信号被处理
            self.msleep(100)

        # 启动文件系统监控
        if self.running:
            self.start_watching()

        # 保持线程运行
        while self.running:
            self.msleep(1000)  # 每秒检查一次

        self.stop_watching()


class FolderEventHandler(FileSystemEventHandler):
    """文件系统事件处理器 with event debouncing"""

    def __init__(self, watcher: CC_FolderWatcher):
        super().__init__()
        self.watcher = watcher

        # Event debouncing: track last event time for each file
        self._last_event_time: Dict[Path, float] = {}
        self._event_cooldown = 1.0  # seconds - ignore events within this window

        # Track if a file is currently being created (to ignore immediate modify events)
        self._recently_created: Dict[Path, float] = {}
        self._creation_grace_period = 2.0  # seconds - ignore modify events after creation

    def _should_process_event(self, path: Path, event_type: str) -> bool:
        """Check if enough time has passed since last event for this file"""
        current_time = time.time()

        # Special handling for modify events after creation
        if event_type == 'modified':
            # If file was recently created, ignore modify events during grace period
            if path in self._recently_created:
                time_since_creation = current_time - self._recently_created[path]
                if time_since_creation < self._creation_grace_period:
                    return False
                else:
                    # Grace period expired, remove from tracking
                    del self._recently_created[path]

        # General debouncing: check last event time
        event_key = path
        if event_key in self._last_event_time:
            time_since_last = current_time - self._last_event_time[event_key]
            if time_since_last < self._event_cooldown:
                return False

        # Update last event time
        self._last_event_time[event_key] = current_time
        return True

    def on_created(self, event: FileSystemEvent):
        """文件创建事件"""
        if not event.is_directory:
            path = Path(event.src_path)
            if self.watcher.is_image(path):
                if not self._should_process_event(path, 'created'):
                    return

                logger.info(f"[FolderWatcher] New photo detected: {path.name}")
                self.watcher.known_photos.add(path)

                # Track creation time to ignore immediate modify events
                self._recently_created[path] = time.time()

                self.watcher.new_photos_found.emit([path])

    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件"""
        if not event.is_directory:
            path = Path(event.src_path)
            if path in self.watcher.known_photos:
                if not self._should_process_event(path, 'deleted'):
                    return

                logger.info(f"[FolderWatcher] Photo deleted: {path.name}")
                self.watcher.known_photos.discard(path)

                # Clean up tracking
                self._last_event_time.pop(path, None)
                self._recently_created.pop(path, None)

                self.watcher.photos_removed.emit([path])

    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if not event.is_directory:
            path = Path(event.src_path)
            if self.watcher.is_image(path) and path in self.watcher.known_photos:
                if not self._should_process_event(path, 'modified'):
                    return

                logger.info(f"[FolderWatcher] Photo modified: {path.name}")
                self.watcher.photos_modified.emit([path])
