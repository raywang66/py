# macOS Data Directory Configuration

## Summary

Modified `CC_Main.py` to store ChromaCloud data files (`chromacloud.db` and `chromacloud.log`) in `~/CC` when running on macOS. This is especially useful when the source code folder is shared via SMB.

## Changes Made

### 1. Platform Detection Function
Added `get_data_directory()` function that:
- Detects the operating system using `platform.system()`
- Returns `~/CC` for macOS (Darwin)
- Returns script directory for Windows/Linux
- Automatically creates the `~/CC` directory if it doesn't exist

### 2. Data File Paths
Created global constants:
- `DATA_DIR`: Platform-specific data directory
- `LOG_FILE`: Full path to `chromacloud.log`
- `DB_FILE`: Full path to `chromacloud.db`

### 3. Updated Logging Configuration
- Changed log file path from `"chromacloud.log"` to `str(LOG_FILE)`
- Log file now goes to `~/CC/chromacloud.log` on macOS

### 4. Updated Database Initialization
- Changed `self.db = CC_Database()` to `self.db = CC_Database(db_path=DB_FILE)`
- Database now stored at `~/CC/chromacloud.db` on macOS

### 5. Added Logging Messages
Added startup log messages to show where data files are stored:
```python
logger.info(f"ChromaCloud data directory: {DATA_DIR}")
logger.info(f"Database: {DB_FILE}")
logger.info(f"Log file: {LOG_FILE}")
```

## Platform Behavior

### macOS (Darwin)
- Data directory: `~/CC/` (e.g., `/Users/rwang/CC/`)
- Database: `~/CC/chromacloud.db`
- Log file: `~/CC/chromacloud.log`

### Windows
- Data directory: Script directory (e.g., `C:\Users\rwang\lc_sln\py\`)
- Database: `C:\Users\rwang\lc_sln\py\chromacloud.db`
- Log file: `C:\Users\rwang\lc_sln\py\chromacloud.log`

### Linux
- Data directory: Script directory
- Database: `<script_dir>/chromacloud.db`
- Log file: `<script_dir>/chromacloud.log`

## Benefits

1. **SMB-Friendly**: Separates data files from code when source is on network share
2. **Clean Separation**: Code stays in shared folder, data stays local
3. **Performance**: Local storage for database = better I/O performance
4. **Automatic Setup**: Directory is created automatically on first run
5. **Backward Compatible**: Windows/Linux behavior unchanged

## Usage

When running ChromaCloud on macOS:

1. Clone/pull your ChromaCloud repository from GitHub
2. Source code can be on SMB share: `/Volumes/shared/ChromaCloud/`
3. Run: `python CC_Main.py`
4. Data files automatically stored in `~/CC/`:
   - `~/CC/chromacloud.db`
   - `~/CC/chromacloud.log`

The startup log will confirm the paths:
```
ChromaCloud data directory: /Users/rwang/CC
Database: /Users/rwang/CC/chromacloud.db
Log file: /Users/rwang/CC/chromacloud.log
```

## Note

The `~/CC` directory is also used by the `install_cc.py` script when you run:
```bash
python install_cc.py --venv ~/CC
```

This creates a consistent location for ChromaCloud-related files on macOS.
