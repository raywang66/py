"""
ChromaCloud (CC) - Auto Analyzer Module
Author: Senior Software Architect
Date: February 2026

Background analysis queue for automatic photo processing.
"""

import logging
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Dict
import pickle
from PySide6.QtCore import QThread, Signal
import numpy as np

logger = logging.getLogger("CC_AutoAnalyzer")


class CC_AutoAnalyzer(QThread):
    """自动分析队列，后台处理新照片"""

    # 信号
    analysis_complete = Signal(int, dict)  # photo_id, results
    analysis_failed = Signal(int, str)     # photo_id, error_message
    queue_progress = Signal(int, int)      # current, total
    status_update = Signal(str)            # status message

    def __init__(self, processor, db_path):
        super().__init__()
        # ⚠️ DO NOT use the passed processor - MediaPipe is NOT thread-safe!
        # We will create our own processor instance in run() thread
        self.db_path = db_path      # Path to database file
        self.processor = None       # Will be created in run() thread (thread-safe)
        self.db = None              # Will be created in run() thread
        self.queue = Queue()
        self.running = True
        self.current_count = 0
        self.total_count = 0

    def add_photo(self, photo_path: Path, album_id: int):
        """添加照片到分析队列"""
        self.queue.put((photo_path, album_id))
        self.total_count += 1
        logger.info(f"[AutoAnalyzer] Added to queue: {photo_path.name} (Queue size: {self.queue.qsize()})")

    def stop(self):
        """停止分析线程"""
        self.running = False
        logger.info("[AutoAnalyzer] Stopping...")

    def run(self):
        """后台处理队列中的照片"""
        logger.info("[AutoAnalyzer] Started")

        # 在此线程中创建数据库连接（线程安全）
        from CC_Database import CC_Database
        self.db = CC_Database(self.db_path)
        logger.info("[AutoAnalyzer] Created thread-local database connection")

        # 🔧 FIX: Create thread-local processor instance
        # MediaPipe FaceMesh is NOT thread-safe!
        # Each thread must have its own processor instance
        from CC_SkinProcessor import CC_SkinProcessor
        self.processor = CC_SkinProcessor()
        logger.info("[AutoAnalyzer] ✅ Created thread-local CC_SkinProcessor (MediaPipe face detection enabled)")

        try:
            while self.running:
                try:
                    # 从队列获取任务（1秒超时）
                    photo_path, album_id = self.queue.get(timeout=1)

                    self.current_count += 1
                    self.queue_progress.emit(self.current_count, self.total_count)
                    self.status_update.emit(f"Analyzing: {photo_path.name}")

                    # 添加到数据库
                    try:
                        photo_id = self.db.add_photo(photo_path)
                        self.db.add_photo_to_album(photo_id, album_id)
                    except Exception as e:
                        logger.error(f"[AutoAnalyzer] Database error for {photo_path.name}: {e}")
                        self.analysis_failed.emit(-1, f"Database error: {e}")
                        continue

                    # 检查是否已分析过
                    existing = self.db.get_analysis(photo_id)
                    if existing and existing.get('face_detected'):
                        logger.info(f"[AutoAnalyzer] Already analyzed: {photo_path.name}")
                        self.analysis_complete.emit(photo_id, dict(existing))
                        continue

                    # 分析照片
                    try:
                        logger.info(f"[AutoAnalyzer] 🔍 Analyzing: {photo_path.name}")
                        image_rgb = self.processor._load_image(photo_path)
                        logger.info(f"[AutoAnalyzer]   Image loaded: {image_rgb.shape}")

                        point_cloud, mask = self.processor.process_image(image_rgb, return_mask=True)

                        # 🔧 Detailed logging for verification
                        mask_coverage = mask.sum() / mask.size * 100
                        logger.info(f"[AutoAnalyzer]   Face mask coverage: {mask_coverage:.2f}%")
                        logger.info(f"[AutoAnalyzer]   Skin pixels extracted: {len(point_cloud)}")

                        if len(point_cloud) > 0:
                            # 计算统计数据
                            results = self._calculate_statistics(point_cloud, mask)

                            # 保存到数据库
                            point_cloud_bytes = pickle.dumps(point_cloud)
                            results['point_cloud_data'] = point_cloud_bytes
                            self.db.save_analysis(photo_id, results)

                            logger.info(f"[AutoAnalyzer] ✅ Analysis complete: {photo_path.name}")
                            logger.info(f"[AutoAnalyzer]   Hue mean: {results['hue_mean']:.2f}, Saturation: {results['saturation_mean']:.2f}")
                            self.analysis_complete.emit(photo_id, results)
                        else:
                            logger.warning(f"[AutoAnalyzer] No face detected: {photo_path.name}")
                            # 仍然保存结果，标记为未检测到人脸
                            results = {'face_detected': False}
                            self.db.save_analysis(photo_id, results)
                            self.analysis_failed.emit(photo_id, "No face detected")

                    except Exception as e:
                        error_msg = f"Analysis error: {e}"
                        logger.error(f"[AutoAnalyzer] {error_msg} for {photo_path.name}", exc_info=True)
                        self.analysis_failed.emit(photo_id, error_msg)

                except Empty:
                    # 队列为空，继续等待
                    continue
                except Exception as e:
                    logger.error(f"[AutoAnalyzer] Unexpected error: {e}", exc_info=True)

        finally:
            # 关闭数据库连接
            if self.db:
                self.db.close()
                logger.info("[AutoAnalyzer] Closed database connection")
            logger.info("[AutoAnalyzer] Stopped")

    def _calculate_statistics(self, point_cloud: np.ndarray, mask: np.ndarray) -> Dict:
        """计算统计数据（与 CC_Main.py 中的逻辑相同）"""

        # 基本统计
        h_mean = point_cloud[:, 0].mean()
        h_std = point_cloud[:, 0].std()
        s_mean = point_cloud[:, 1].mean()
        l_mean = point_cloud[:, 2].mean()

        # Lightness 分布 (3 ranges) - multiply by 100 for percentage
        lightness = point_cloud[:, 2]
        low_light = (lightness < 0.33).sum() / len(lightness) * 100
        mid_light = ((lightness >= 0.33) & (lightness < 0.67)).sum() / len(lightness) * 100
        high_light = (lightness >= 0.67).sum() / len(lightness) * 100

        # Hue 分布 (6 ranges) - multiply by 100 for percentage
        # ⚠️ IMPORTANT: point_cloud[:, 0] is already in degrees [0, 360]!
        # DO NOT multiply by 360 (that was the bug causing wrong Hue results)
        hue = point_cloud[:, 0]  # Already in degrees [0, 360]
        hue_very_red = (((hue >= 0) & (hue < 10)) | (hue >= 350)).sum() / len(hue) * 100
        hue_red_orange = ((hue >= 10) & (hue < 20)).sum() / len(hue) * 100
        hue_normal = ((hue >= 20) & (hue < 30)).sum() / len(hue) * 100
        hue_yellow = ((hue >= 30) & (hue < 40)).sum() / len(hue) * 100
        hue_very_yellow = ((hue >= 40) & (hue < 60)).sum() / len(hue) * 100
        hue_abnormal = ((hue >= 60) & (hue < 350)).sum() / len(hue) * 100

        # Saturation 分布 (5 ranges) - multiply by 100 for percentage
        saturation = point_cloud[:, 1] * 100  # 转换为百分比
        sat_very_low = (saturation < 15).sum() / len(saturation) * 100
        sat_low = ((saturation >= 15) & (saturation < 30)).sum() / len(saturation) * 100
        sat_normal = ((saturation >= 30) & (saturation < 50)).sum() / len(saturation) * 100
        sat_high = ((saturation >= 50) & (saturation < 70)).sum() / len(saturation) * 100
        sat_very_high = (saturation >= 70).sum() / len(saturation) * 100

        results = {
            'face_detected': True,
            'num_points': len(point_cloud),
            'mask_coverage': mask.sum() / mask.size,
            'hue_mean': float(h_mean),
            'hue_std': float(h_std),
            'saturation_mean': float(s_mean),
            'lightness_mean': float(l_mean),
            'lightness_low': float(low_light),
            'lightness_mid': float(mid_light),
            'lightness_high': float(high_light),
            'hue_very_red': float(hue_very_red),
            'hue_red_orange': float(hue_red_orange),
            'hue_normal': float(hue_normal),
            'hue_yellow': float(hue_yellow),
            'hue_very_yellow': float(hue_very_yellow),
            'hue_abnormal': float(hue_abnormal),
            'sat_very_low': float(sat_very_low),
            'sat_low': float(sat_low),
            'sat_normal': float(sat_normal),
            'sat_high': float(sat_high),
            'sat_very_high': float(sat_very_high),
        }

        return results
