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
                lightness_low, lightness_mid, lightness_high, point_cloud_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
