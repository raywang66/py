"""
Clean duplicate analysis results from database
Keep only the most recent analysis for each photo
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "chromacloud.db"

def clean_duplicates():
    """Remove duplicate analysis results, keep only the latest"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find photos with multiple analysis results
    cursor.execute("""
        SELECT photo_id, COUNT(*) as count
        FROM analysis_results
        GROUP BY photo_id
        HAVING count > 1
    """)

    duplicates = cursor.fetchall()
    logger.info(f"Found {len(duplicates)} photos with duplicate analysis")

    total_deleted = 0
    for photo_id, count in duplicates:
        # Keep only the most recent one
        cursor.execute("""
            DELETE FROM analysis_results
            WHERE photo_id = ? AND id NOT IN (
                SELECT id FROM analysis_results
                WHERE photo_id = ?
                ORDER BY analyzed_at DESC
                LIMIT 1
            )
        """, (photo_id, photo_id))
        deleted = cursor.rowcount
        total_deleted += deleted
        logger.info(f"Photo {photo_id}: deleted {deleted} old analysis records")

    conn.commit()
    conn.close()

    logger.info(f"Total deleted: {total_deleted} duplicate records")
    logger.info("✅ Database cleaned successfully!")

if __name__ == "__main__":
    clean_duplicates()
