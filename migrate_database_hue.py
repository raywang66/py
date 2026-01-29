"""
Database Migration Script - Add Hue Distribution Columns

This script will add the hue distribution columns to your existing database.
Run this after updating the code to ensure your database has all necessary fields.

Date: January 28, 2026
"""

import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def migrate_database(db_path: Path = None):
    """Add hue distribution columns to existing database"""

    if db_path is None:
        db_path = Path(__file__).parent / "chromacloud.db"

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False

    logger.info(f"Migrating database: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(analysis_results)")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Current columns: {columns}")

        columns_to_add = [
            ('hue_very_red', 'REAL DEFAULT 0.0'),
            ('hue_red_orange', 'REAL DEFAULT 0.0'),
            ('hue_normal', 'REAL DEFAULT 0.0'),
            ('hue_yellow', 'REAL DEFAULT 0.0'),
            ('hue_very_yellow', 'REAL DEFAULT 0.0'),
            ('hue_abnormal', 'REAL DEFAULT 0.0')
        ]

        added_count = 0
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                logger.info(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE analysis_results ADD COLUMN {col_name} {col_type}")
                added_count += 1
            else:
                logger.info(f"Column already exists: {col_name}")

        conn.commit()

        # Verify columns were added
        cursor.execute("PRAGMA table_info(analysis_results)")
        new_columns = [row[1] for row in cursor.fetchall()]

        logger.info(f"\n✅ Migration complete!")
        logger.info(f"   Added {added_count} new columns")
        logger.info(f"   Total columns: {len(new_columns)}")

        # Show sample of what needs to be re-analyzed
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN hue_very_red = 0.0 AND hue_normal = 0.0 THEN 1 ELSE 0 END) as needs_reanalysis
            FROM analysis_results
        """)
        row = cursor.fetchone()

        if row[0] > 0:
            logger.info(f"\n📊 Analysis Data:")
            logger.info(f"   Total analyzed photos: {row[0]}")
            logger.info(f"   Need re-analysis: {row[1]}")

            if row[1] > 0:
                logger.warning(f"\n⚠️  {row[1]} photos have no hue distribution data.")
                logger.warning(f"   Please re-analyze these photos to see hue distribution charts.")
                logger.warning(f"   Use 'Batch Analyze' in the main application.")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ChromaCloud Database Migration")
    print("Adding Hue Distribution Columns")
    print("=" * 60)
    print()

    success = migrate_database()

    print()
    if success:
        print("✅ Migration successful!")
        print()
        print("Next steps:")
        print("1. Run the main application (python CC_MainApp_v2_simple.py)")
        print("2. Select an album")
        print("3. Click 'Batch Analyze' to analyze photos")
        print("4. Right-click album → 'View Statistics'")
        print("5. Check the '🌈 Hue Comparison' and '💧 Saturation Comparison' tabs")
    else:
        print("❌ Migration failed!")
        print("Please check the error messages above.")

    print()
    input("Press Enter to exit...")
