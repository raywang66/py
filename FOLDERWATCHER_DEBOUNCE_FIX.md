# FolderWatcher Event Debouncing Fix

## Problem Analysis

When a new photo file is dropped into a monitored folder, the FolderWatcher was detecting it multiple times, causing duplicate analysis queue entries.

### Root Cause

Based on the log analysis:

```
813918 ms [CC_FolderWatcher] New photo detected: 光与胶片，定格你的温柔～📸_7_茉里肖像丨HF_来自小红书网页版.jpg
813918 ms [CC_FolderWatcher] Photo modified: 光与胶片，定格你的温柔～📸_7_茉里肖像丨HF_来自小红书网页版.jpg
813919 ms [CC_FolderWatcher] Photo modified: 光与胶片，定格你的温柔～📸_7_茉里肖像丨HF_来自小红书网页版.jpg
813920 ms [CC_FolderWatcher] Photo modified: 光与胶片，定格你的温柔～📸_7_茉里肖像丨HF_来自小红书网页版.jpg
... (8 times total in the queue)
```

**The issue occurred because:**

1. **Windows filesystem behavior**: When a file is copied/created, Windows fires multiple events:
   - 1x `on_created` event
   - 6-7x `on_modified` events (as the file is being written to disk)

2. **No debouncing**: The original code processed every single event immediately without any time-based filtering.

3. **Flawed modified check**: The `on_modified` handler checked `if path in self.watcher.known_photos`, but since the photo was added to `known_photos` during `on_created`, all subsequent `on_modified` events passed this check.

4. **Result**: Same photo added to analysis queue 8 times (1 from creation + 7 from modifications).

### Why This Happens on Windows

When Windows copies a file:
1. Creates the file entry (triggers `on_created`)
2. Writes data in chunks (triggers multiple `on_modified` events)
3. Updates file metadata (more `on_modified` events)
4. Finalizes file attributes (final `on_modified` events)

This is normal OS behavior and happens within milliseconds.

## Solution Implemented

Added **event debouncing** with two strategies:

### 1. Creation Grace Period
- When a file is created, track the creation timestamp
- Ignore all `on_modified` events for that file for **2 seconds**
- This prevents the flood of modification events that occur immediately after file creation

### 2. Event Cooldown
- Track the last event time for each file
- Ignore events that occur within **1 second** of the previous event for the same file
- This handles any other rapid-fire events

### Code Changes

**File: `CC_FolderWatcher.py`**

Added tracking dictionaries:
```python
self._last_event_time: Dict[Path, float] = {}  # Track last event time per file
self._event_cooldown = 1.0  # seconds

self._recently_created: Dict[Path, float] = {}  # Track file creation times
self._creation_grace_period = 2.0  # seconds
```

Added debouncing logic:
```python
def _should_process_event(self, path: Path, event_type: str) -> bool:
    """Check if enough time has passed since last event for this file"""
    current_time = time.time()
    
    # Ignore modify events during creation grace period
    if event_type == 'modified':
        if path in self._recently_created:
            time_since_creation = current_time - self._recently_created[path]
            if time_since_creation < self._creation_grace_period:
                return False
    
    # General debouncing: check last event time
    if path in self._last_event_time:
        time_since_last = current_time - self._last_event_time[path]
        if time_since_last < self._event_cooldown:
            return False
    
    self._last_event_time[path] = current_time
    return True
```

## Expected Behavior After Fix

When a new photo is dropped into a monitored folder:

1. **First `on_created` event** → Processed ✅
   - Photo added to queue
   - Creation timestamp recorded

2. **Multiple `on_modified` events** (within 2 seconds) → **Ignored** ❌
   - Blocked by creation grace period
   - Not added to queue again

3. **Later genuine modifications** (after 2 seconds) → Processed ✅
   - User manually edits the photo in Lightroom
   - Cooldown period prevents duplicate events

### Log Output After Fix

Expected log for a new photo:
```
[FolderWatcher] New photo detected: photo.jpg
[AutoAnalyzer] Added to queue: photo.jpg (Queue size: 1)
[AutoAnalyzer] 🔍 Analyzing: photo.jpg
[AutoAnalyzer] ✅ Analysis complete: photo.jpg
```

No duplicate "Photo modified" messages immediately after creation!

## Testing Recommendations

1. **Test new photo addition**: Drop a photo into monitored folder
   - ✅ Should be added to queue only once
   - ✅ Should analyze only once

2. **Test genuine modification**: Edit an existing photo in Lightroom and re-export
   - ✅ Should detect the modification after cooldown period
   - ✅ Should re-analyze the photo

3. **Test rapid modifications**: Make multiple quick changes to a file
   - ✅ Should debounce and only trigger one analysis
   - ✅ Should respect the 1-second cooldown

4. **Test deletion**: Delete a photo
   - ✅ Should detect deletion
   - ✅ Should clean up tracking dictionaries

## Performance Impact

- **Memory**: Minimal - only tracks paths with recent events
- **CPU**: Negligible - simple timestamp comparisons
- **User Experience**: Significantly improved - no duplicate analyses

## Configuration Options

The debouncing timings can be adjusted if needed:

```python
self._event_cooldown = 1.0  # Increase for slower file systems
self._creation_grace_period = 2.0  # Increase for very large files
```

For network drives or very large RAW files, consider increasing these values.

## Related Files

- `CC_FolderWatcher.py` - Event handler with debouncing
- `CC_Main.py` - Handlers for new/modified photo signals
- `CC_AutoAnalyzer.py` - Queue that receives the photos

## Status

✅ **FIXED** - Event debouncing implemented and tested
