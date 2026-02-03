"""
ChromaCloud (CC) - Database Module
Author: Senior Software Architect
Date: January 2026

SQLite database for managing albums, projects, and analysis results.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger("CC_Database")


class CC_Database:
    """Database manager for ChromaCloud"""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection"""
        if db_path is None:
            db_path = Path(__file__).parent / "chromacloud.db"

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries

        self._create_tables()

        # Clean up orphaned thumbnail cache on startup
        # Ensures cache integrity - thumbnails must have corresponding photos!
        self.cleanup_orphaned_thumbnails()

        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Albums table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                folder_path TEXT,
                auto_scan INTEGER DEFAULT 0,
                last_scan_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Photos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Album-Photo relationships (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS album_photos (
                album_id INTEGER,
                photo_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (album_id, photo_id),
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
            )
        """)

        # Project-Photo relationships (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_photos (
                project_id INTEGER,
                photo_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, photo_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
            )
        """)

        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_id INTEGER NOT NULL,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                face_detected BOOLEAN,
                num_points INTEGER,
                mask_coverage REAL,
                hue_mean REAL,
                hue_std REAL,
                saturation_mean REAL,
                lightness_mean REAL,
                lightness_low REAL,
                lightness_mid REAL,
                lightness_high REAL,
                hue_very_red REAL,
                hue_red_orange REAL,
                hue_normal REAL,
                hue_yellow REAL,
                hue_very_yellow REAL,
                hue_abnormal REAL,
                sat_very_low REAL,
                sat_low REAL,
                sat_normal REAL,
                sat_high REAL,
                sat_very_high REAL,
                point_cloud_data BLOB,
                FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

        # Add missing columns if they don't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN lightness_low REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN lightness_mid REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN lightness_high REAL DEFAULT 0.0")
            self.conn.commit()
            logger.info("Added lightness distribution columns to existing database")
        except sqlite3.OperationalError:
            # Columns already exist
            pass

        # Add hue distribution columns (for existing databases)
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN hue_very_red REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN hue_red_orange REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN hue_normal REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN hue_yellow REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN hue_very_yellow REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN hue_abnormal REAL DEFAULT 0.0")
            self.conn.commit()
            logger.info("Added hue distribution columns to existing database")
        except sqlite3.OperationalError:
            # Columns already exist
            pass

        # Add saturation distribution columns (for existing databases)
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN sat_very_low REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN sat_low REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN sat_normal REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN sat_high REAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN sat_very_high REAL DEFAULT 0.0")
            self.conn.commit()
            logger.info("Added saturation distribution columns to existing database")
        except sqlite3.OperationalError:
            # Columns already exist
            pass

        # Add folder monitoring fields to albums table (for existing databases)
        try:
            cursor.execute("ALTER TABLE albums ADD COLUMN folder_path TEXT")
            cursor.execute("ALTER TABLE albums ADD COLUMN auto_scan INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE albums ADD COLUMN last_scan_time TIMESTAMP")
            self.conn.commit()
            logger.info("Added folder monitoring columns to albums table")
        except sqlite3.OperationalError:
            # Columns already exist
            pass

        # Create indexes for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_albums_folder ON albums(folder_path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_photos_path ON photos(file_path)")
            self.conn.commit()
            logger.info("Created performance indexes")
        except sqlite3.OperationalError:
            pass

        # Thumbnail cache table for fast loading
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thumbnail_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                photo_path TEXT NOT NULL UNIQUE,
                photo_mtime REAL NOT NULL,
                thumbnail_data BLOB NOT NULL,
                thumbnail_width INTEGER NOT NULL,
                thumbnail_height INTEGER NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_thumbnail_path ON thumbnail_cache(photo_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_thumbnail_mtime ON thumbnail_cache(photo_mtime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_thumbnail_accessed ON thumbnail_cache(accessed_at)")

        # Add file_mtime to photos table for change detection
        try:
            cursor.execute("ALTER TABLE photos ADD COLUMN file_mtime REAL")
            self.conn.commit()
            logger.info("Added file_mtime column to photos table")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Folder cache table for performance optimization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folder_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id INTEGER NOT NULL,
                folder_path TEXT NOT NULL,
                parent_folder_path TEXT,
                photo_count INTEGER DEFAULT 0,
                direct_photo_count INTEGER DEFAULT 0,
                last_scan_time REAL,
                FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for folder cache
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_folder_cache_album ON folder_cache(album_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_folder_cache_path ON folder_cache(folder_path)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_folder_cache_unique ON folder_cache(album_id, folder_path)")
            self.conn.commit()
            logger.info("Created folder cache table and indexes")
        except sqlite3.OperationalError:
            pass

    # ========== Album Operations ==========

    def create_album(self, name: str, description: str = "") -> int:
        """Create a new album"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO albums (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        logger.info(f"Created album: {name}")
        return cursor.lastrowid

    def get_all_albums(self) -> List[Dict]:
        """Get all albums"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.*, COUNT(ap.photo_id) as photo_count
            FROM albums a
            LEFT JOIN album_photos ap ON a.id = ap.album_id
            GROUP BY a.id
            ORDER BY a.name
        """)
        return [dict(row) for row in cursor.fetchall()]

    def rename_album(self, album_id: int, new_name: str):
        """Rename an album"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE albums SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_name, album_id)
        )
        self.conn.commit()
        logger.info(f"Renamed album {album_id} to: {new_name}")

    def delete_album(self, album_id: int):
        """Delete an album (photos are not deleted)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM albums WHERE id = ?", (album_id,))
        self.conn.commit()
        logger.info(f"Deleted album: {album_id}")

    # ========== Project Operations ==========

    def create_project(self, name: str, description: str = "") -> int:
        """Create a new project"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        logger.info(f"Created project: {name}")
        return cursor.lastrowid

    def get_all_projects(self) -> List[Dict]:
        """Get all projects"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(pp.photo_id) as photo_count
            FROM projects p
            LEFT JOIN project_photos pp ON p.id = pp.project_id
            GROUP BY p.id
            ORDER BY p.name
        """)
        return [dict(row) for row in cursor.fetchall()]

    def rename_project(self, project_id: int, new_name: str):
        """Rename a project"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_name, project_id)
        )
        self.conn.commit()
        logger.info(f"Renamed project {project_id} to: {new_name}")

    def delete_project(self, project_id: int):
        """Delete a project (photos are not deleted)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()
        logger.info(f"Deleted project: {project_id}")

    # ========== Photo Operations ==========

    def add_photo(self, file_path: Path, width: int = None, height: int = None) -> int:
        """Add a photo to the database"""
        cursor = self.conn.cursor()

        # Check if photo already exists
        cursor.execute("SELECT id FROM photos WHERE file_path = ?", (str(file_path),))
        existing = cursor.fetchone()
        if existing:
            return existing['id']

        file_size = file_path.stat().st_size
        cursor.execute("""
            INSERT INTO photos (file_path, file_name, file_size, width, height)
            VALUES (?, ?, ?, ?, ?)
        """, (str(file_path), file_path.name, file_size, width, height))
        self.conn.commit()
        return cursor.lastrowid

    def add_photo_to_album(self, photo_id: int, album_id: int):
        """Add a photo to an album"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO album_photos (album_id, photo_id) VALUES (?, ?)",
            (album_id, photo_id)
        )
        self.conn.commit()

    def add_photo_to_project(self, photo_id: int, project_id: int):
        """Add a photo to a project"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO project_photos (project_id, photo_id) VALUES (?, ?)",
            (project_id, photo_id)
        )
        self.conn.commit()

    def get_album_photos(self, album_id: int) -> List[Dict]:
        """Get all photos in an album"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.* FROM photos p
            JOIN album_photos ap ON p.id = ap.photo_id
            WHERE ap.album_id = ?
            ORDER BY ap.added_at DESC
        """, (album_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_project_photos(self, project_id: int) -> List[Dict]:
        """Get all photos in a project"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.* FROM photos p
            JOIN project_photos pp ON p.id = pp.photo_id
            WHERE pp.project_id = ?
            ORDER BY pp.added_at DESC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_photos(self) -> List[Dict]:
        """Get all photos from database - ONLY shows photos that have been explicitly added"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM photos
            ORDER BY added_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    # ========== Analysis Operations ==========

    def save_analysis(self, photo_id: int, results: Dict, point_cloud: bytes = None):
        """Save analysis results for a photo"""
        cursor = self.conn.cursor()

        # Delete old analysis results for this photo to avoid duplicates
        cursor.execute("DELETE FROM analysis_results WHERE photo_id = ?", (photo_id,))

        # Ensure all numeric values are properly typed
        cursor.execute("""
            INSERT INTO analysis_results (
                photo_id, face_detected, num_points, mask_coverage,
                hue_mean, hue_std, saturation_mean, lightness_mean, 
                lightness_low, lightness_mid, lightness_high,
                hue_very_red, hue_red_orange, hue_normal, 
                hue_yellow, hue_very_yellow, hue_abnormal,
                sat_very_low, sat_low, sat_normal, sat_high, sat_very_high,
                point_cloud_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(photo_id),
            bool(results.get('face_detected', False)),
            int(results.get('num_points', 0)),
            float(results.get('mask_coverage', 0.0)),
            float(results.get('hue_mean', 0.0)),
            float(results.get('hue_std', 0.0)),
            float(results.get('saturation_mean', 0.0)),
            float(results.get('lightness_mean', 0.0)),
            float(results.get('lightness_low', 0.0)),
            float(results.get('lightness_mid', 0.0)),
            float(results.get('lightness_high', 0.0)),
            float(results.get('hue_very_red', 0.0)),
            float(results.get('hue_red_orange', 0.0)),
            float(results.get('hue_normal', 0.0)),
            float(results.get('hue_yellow', 0.0)),
            float(results.get('hue_very_yellow', 0.0)),
            float(results.get('hue_abnormal', 0.0)),
            float(results.get('sat_very_low', 0.0)),
            float(results.get('sat_low', 0.0)),
            float(results.get('sat_normal', 0.0)),
            float(results.get('sat_high', 0.0)),
            float(results.get('sat_very_high', 0.0)),
            point_cloud
        ))
        self.conn.commit()
        logger.info(f"Saved analysis for photo: {photo_id}")

    def get_analysis(self, photo_id: int) -> Optional[Dict]:
        """Get the latest analysis for a photo"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM analysis_results
            WHERE photo_id = ?
            ORDER BY analyzed_at DESC
            LIMIT 1
        """, (photo_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_album_statistics(self, album_id: int) -> Dict:
        """Get aggregated statistics for an album"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT ar.photo_id) as analyzed_count,
                AVG(ar.hue_mean) as avg_hue,
                AVG(ar.saturation_mean) as avg_saturation,
                AVG(ar.lightness_mean) as avg_lightness,
                MIN(ar.hue_mean) as min_hue,
                MAX(ar.hue_mean) as max_hue
            FROM analysis_results ar
            JOIN album_photos ap ON ar.photo_id = ap.photo_id
            WHERE ap.album_id = ? AND ar.face_detected = 1
        """, (album_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

    def get_album_detailed_statistics(self, album_id: int) -> List[Dict]:
        """Get detailed statistics for each photo in an album"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                p.file_name as photo_name,
                p.file_path,
                ar.hue_mean,
                ar.hue_std,
                ar.saturation_mean,
                ar.lightness_mean,
                ar.lightness_low,
                ar.lightness_mid,
                ar.lightness_high,
                ar.hue_very_red,
                ar.hue_red_orange,
                ar.hue_normal,
                ar.hue_yellow,
                ar.hue_very_yellow,
                ar.hue_abnormal,
                ar.sat_very_low,
                ar.sat_low,
                ar.sat_normal,
                ar.sat_high,
                ar.sat_very_high,
                ar.num_points,
                ar.mask_coverage,
                ar.analyzed_at
            FROM analysis_results ar
            JOIN album_photos ap ON ar.photo_id = ap.photo_id
            JOIN photos p ON ar.photo_id = p.id
            WHERE ap.album_id = ? AND ar.face_detected = 1
            ORDER BY ar.analyzed_at DESC
        """, (album_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_project_statistics(self, project_id: int) -> Dict:
        """Get aggregated statistics for a project"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT ar.photo_id) as analyzed_count,
                AVG(ar.hue_mean) as avg_hue,
                AVG(ar.saturation_mean) as avg_saturation,
                AVG(ar.lightness_mean) as avg_lightness,
                MIN(ar.hue_mean) as min_hue,
                MAX(ar.hue_mean) as max_hue
            FROM analysis_results ar
            JOIN project_photos pp ON ar.photo_id = pp.photo_id
            WHERE pp.project_id = ? AND ar.face_detected = 1
        """, (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

    # ========== Folder Cache Operations (Performance Optimization) ==========

    def get_folder_structure(self, album_id: int) -> List[Dict]:
        """Get cached folder structure for an album (instant)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT folder_path, parent_folder_path, 
                   photo_count, direct_photo_count, last_scan_time
            FROM folder_cache
            WHERE album_id = ?
            ORDER BY folder_path
        """, (album_id,))
        return [dict(row) for row in cursor.fetchall()]

    def update_folder_cache(self, album_id: int, folder_path: str,
                           photo_count: int, direct_count: int,
                           parent_path: Optional[str] = None):
        """Update folder cache entry"""
        import time
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO folder_cache 
            (album_id, folder_path, parent_folder_path, photo_count, direct_photo_count, last_scan_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (album_id, folder_path, parent_path, photo_count, direct_count, time.time()))
        self.conn.commit()

    def clear_folder_cache(self, album_id: int):
        """Clear folder cache for an album"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM folder_cache WHERE album_id = ?", (album_id,))
        self.conn.commit()

    def has_folder_cache(self, album_id: int) -> bool:
        """Check if album has cached folder structure"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM folder_cache WHERE album_id = ?", (album_id,))
        count = cursor.fetchone()[0]
        return count > 0

    # ========== Thumbnail Cache Methods ==========

    def get_thumbnail_cache(self, photo_path: str) -> Optional[Dict]:
        """
        Get cached thumbnail for a photo
        Returns dict with thumbnail_data, photo_mtime, width, height or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT thumbnail_data, photo_mtime, thumbnail_width, thumbnail_height
            FROM thumbnail_cache
            WHERE photo_path = ?
        """, (photo_path,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def save_thumbnail_cache(self, photo_path: str, photo_mtime: float,
                            thumbnail_data: bytes, width: int, height: int):
        """Save thumbnail to cache"""
        import time
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO thumbnail_cache 
            (photo_path, photo_mtime, thumbnail_data, thumbnail_width, thumbnail_height,
             created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (photo_path, photo_mtime, thumbnail_data, width, height, time.time(), time.time()))
        self.conn.commit()

    def update_thumbnail_access_time(self, photo_path: str):
        """Update last accessed time for LRU cache management"""
        import time
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE thumbnail_cache 
            SET accessed_at = ? 
            WHERE photo_path = ?
        """, (time.time(), photo_path))
        self.conn.commit()

    def invalidate_thumbnail_cache(self, photo_path: str):
        """Remove thumbnail from cache (e.g., when file is modified)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM thumbnail_cache WHERE photo_path = ?", (photo_path,))
        self.conn.commit()

    def clear_thumbnail_cache(self):
        """Clear all thumbnail cache (for maintenance)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM thumbnail_cache")
        self.conn.commit()
        logger.info("Thumbnail cache cleared")

    def get_thumbnail_cache_stats(self) -> Dict:
        """Get thumbnail cache statistics"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as count,
                SUM(LENGTH(thumbnail_data)) as total_size,
                AVG(LENGTH(thumbnail_data)) as avg_size
            FROM thumbnail_cache
        """)
        row = cursor.fetchone()
        return dict(row) if row else {'count': 0, 'total_size': 0, 'avg_size': 0}

    def cleanup_old_thumbnail_cache(self, days: int = 90):
        """
        Clean up thumbnails not accessed for specified days (LRU cleanup)
        """
        import time
        threshold = time.time() - (days * 24 * 3600)
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM thumbnail_cache 
            WHERE accessed_at < ?
        """, (threshold,))
        deleted = cursor.rowcount
        self.conn.commit()
        logger.info(f"Cleaned up {deleted} old thumbnail cache entries")
        return deleted

    def cleanup_orphaned_thumbnails(self):
        """
        Clean up orphaned thumbnail cache entries that have no corresponding photos record.
        Thumbnail cache is PASSIVE - it must be linked to photos table!
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM thumbnail_cache 
            WHERE photo_path NOT IN (SELECT file_path FROM photos)
        """)
        deleted = cursor.rowcount
        self.conn.commit()
        logger.info(f"Cleaned up {deleted} orphaned thumbnail cache entries")
        return deleted

    def update_photo_mtime(self, photo_path: str, mtime: float):
        """Update file modification time for a photo"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE photos 
            SET file_mtime = ? 
            WHERE file_path = ?
        """, (mtime, photo_path))
        self.conn.commit()

    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    # Test database
    logging.basicConfig(level=logging.INFO)

    db = CC_Database(Path("test_chromacloud.db"))

    # Test album operations
    album_id = db.create_album("Test Album", "A test album")
    print(f"Created album: {album_id}")

    albums = db.get_all_albums()
    print(f"All albums: {albums}")

    db.close()
    print("✓ Database test complete")
