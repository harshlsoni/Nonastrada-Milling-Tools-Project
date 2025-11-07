# Progress Sync Fix

## Problem

The frontend progress bar was using simulated timeouts and didn't sync with actual backend processing. This meant:
- Progress bar advanced at fixed intervals regardless of actual work
- Could show "completed" while backend still processing
- No real feedback on what's actually happening

## Solution

Implemented real-time progress tracking using:

### 1. Backend Progress Tracker

Added a global `progress_tracker` dictionary that stores current step for each session:

```python
# Global progress tracker
progress_tracker = {}

# In demo function
session_id = str(uuid.uuid4())
progress_tracker[session_id] = {'step': 'init', 'status': 'active'}

# Update as processing progresses
progress_tracker[session_id] = {'step': 'extract', 'status': 'active'}
progress_tracker[session_id] = {'step': 'spectrogram', 'status': 'active'}
# ... etc
```

### 2. Progress Endpoint

Added `/progress/<session_id>` endpoint that returns current step:

```python
@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get current progress for a session."""
    if session_id in progress_tracker:
        return jsonify(progress_tracker[session_id])
    return jsonify({'step': 'unknown', 'status': 'not_found'}), 404
```

### 3. Frontend Polling

Updated JavaScript to poll backend every 200ms for real progress:

```javascript
// Start polling when demo starts
progressInterval = setInterval(pollProgress, 200);

function pollProgress() {
    fetch('/progress/' + sessionId)
        .then(response => response.json())
        .then(progressData => {
            updateProgress(progressData.step, progressData.status);
        });
}
```

## How It Works

### Flow

1. **User clicks "Run Demo"**
   - Frontend calls `/demo`
   - Backend generates unique `session_id`
   - Backend sets initial progress: `{'step': 'init', 'status': 'active'}`

2. **Backend Processing**
   - As each step completes, backend updates progress tracker:
     - `init` → `extract` → `spectrogram` → `scalogram` → `images` → `model` → `complete`
   - Each update includes status: `active`, `completed`, or `error`

3. **Frontend Polling**
   - Every 200ms, frontend calls `/progress/<session_id>`
   - Gets current step and status
   - Updates UI to match backend state

4. **Completion**
   - Backend sets final step: `{'step': 'complete', 'status': 'completed'}`
   - Frontend stops polling
   - Shows final results

## Progress Steps

The pipeline tracks these steps:

1. **init** - Initialization and data loading
2. **extract** - Extracting force signals from MAT file
3. **spectrogram** - Computing spectrograms (happens during TFR generation)
4. **scalogram** - Computing scalograms (happens during TFR generation)
5. **images** - Processing/saving images
6. **model** - Running model inference
7. **complete** - Processing finished

## Benefits

### Before Fix
- ❌ Progress bar used fake timeouts
- ❌ Could show wrong step
- ❌ No sync with backend
- ❌ Misleading user feedback

### After Fix
- ✅ Real-time backend progress
- ✅ Accurate step display
- ✅ Synced with actual processing
- ✅ True user feedback

## Technical Details

### Polling Frequency
- **200ms intervals** - Good balance between responsiveness and server load
- Can be adjusted if needed (100ms for faster, 500ms for lighter load)

### Session Management
- Each demo run gets unique `session_id`
- Progress tracked per session
- Old sessions remain in memory (could add cleanup if needed)

### Error Handling
- If progress endpoint fails, continues silently
- Doesn't break demo if polling has issues
- Final result still displayed correctly

## Testing

### Test 1: Normal Processing
1. Click "Run Demo"
2. Watch progress bar advance through steps
3. Each step should match backend logging
4. Should complete at "Complete" step

### Test 2: Error Case
1. If images missing (hypothetical)
2. Progress should stop at error step
3. Status should show "error"
4. Warning message displayed

### Test 3: Multiple Demos
1. Run demo multiple times
2. Each should have unique session_id
3. Progress tracked independently
4. No interference between runs

## Performance Impact

- **Minimal overhead**: 200ms polling is lightweight
- **Network traffic**: ~5 requests/second during processing
- **Server load**: Simple dictionary lookup, very fast
- **Memory**: One entry per session (negligible)

## Future Enhancements

### Option 1: Server-Sent Events (SSE)
Instead of polling, push updates from server:
```python
@app.route('/progress-stream/<session_id>')
def progress_stream(session_id):
    def generate():
        while True:
            if session_id in progress_tracker:
                yield f"data: {json.dumps(progress_tracker[session_id])}\n\n"
            time.sleep(0.2)
    return Response(generate(), mimetype='text/event-stream')
```

### Option 2: WebSockets
Real-time bidirectional communication:
- More complex setup
- Better for high-frequency updates
- Overkill for this use case

### Option 3: Progress Percentage
Add percentage complete to each step:
```python
progress_tracker[session_id] = {
    'step': 'spectrogram',
    'status': 'active',
    'percent': 45
}
```

### Option 4: Detailed Sub-steps
Track progress within each step:
```python
progress_tracker[session_id] = {
    'step': 'spectrogram',
    'status': 'active',
    'detail': 'Processing X-axis (1/3)'
}
```

## Cleanup (Optional)

To prevent memory growth, could add session cleanup:

```python
import time
from threading import Thread

# Add timestamp to progress
progress_tracker[session_id] = {
    'step': 'init',
    'status': 'active',
    'timestamp': time.time()
}

# Cleanup old sessions (run in background)
def cleanup_old_sessions():
    while True:
        time.sleep(300)  # Every 5 minutes
        current_time = time.time()
        old_sessions = [
            sid for sid, data in progress_tracker.items()
            if current_time - data.get('timestamp', 0) > 3600  # 1 hour old
        ]
        for sid in old_sessions:
            del progress_tracker[sid]

# Start cleanup thread
Thread(target=cleanup_old_sessions, daemon=True).start()
```

## Summary

**Problem**: Progress bar didn't sync with backend  
**Solution**: Real-time polling of backend progress  
**Result**: Accurate, synchronized progress display  
**Impact**: Minimal overhead, better UX

The progress bar now accurately reflects what's happening in the backend!
