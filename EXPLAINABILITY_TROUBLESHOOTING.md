# Explainability Module - Troubleshooting Guide

## Issue: "Explainability module not available"

### ✅ FIXED

The import issue has been resolved. The problem was in `Code/Explainability/__init__.py` trying to import modules that don't exist yet.

### What Was Fixed

1. **Updated `Code/Explainability/__init__.py`**
   - Removed imports of non-existent modules
   - Only imports `simple_explainer.py` (which exists)
   - Added try/except for graceful handling

2. **Updated `Code/flask_app.py`**
   - Added fallback import logic
   - Better error messages
   - Handles both relative and absolute imports

### Verify It Works

Run this test:
```bash
python test_explainability_import.py
```

You should see:
```
✓ SUCCESS: All functions imported successfully!
✓ analyze_prediction_simple() works
✓ create_contribution_breakdown_simple() works
✓ format_explanation_text() works
✓ visualize_contributions_simple() works

ALL TESTS PASSED!
```

### Now Run the App

```bash
python Code/flask_app.py
```

You should see in the console:
```
[INFO] Explainability module loaded successfully
```

If you see:
```
[WARNING] Explainability module not available
```

Then follow the troubleshooting steps below.

---

## Troubleshooting Steps

### Step 1: Verify Files Exist

```bash
# Check if files exist
ls Code/Explainability/
```

You should see:
- `__init__.py`
- `simple_explainer.py`
- `modality_attribution.py` (optional, for future use)

### Step 2: Test Import Directly

```bash
python -c "import sys; sys.path.insert(0, 'Code'); from Explainability.simple_explainer import analyze_prediction_simple; print('SUCCESS')"
```

If this fails, check:
1. Are you in the project root directory?
2. Does `Code/Explainability/simple_explainer.py` exist?
3. Is there a syntax error in `simple_explainer.py`?

### Step 3: Check Python Path

```python
python -c "import sys; print('\n'.join(sys.path))"
```

Make sure the `Code` directory or project root is in the path.

### Step 4: Check for Syntax Errors

```bash
python -m py_compile Code/Explainability/simple_explainer.py
```

If there are syntax errors, they'll be shown here.

### Step 5: Run Test Script

```bash
python test_explainability_import.py
```

This will give you detailed error messages.

---

## Common Issues

### Issue 1: "No module named 'Explainability'"

**Cause**: Python can't find the Explainability folder

**Solution**:
```python
# Make sure you're running from project root
cd /path/to/Nonastrada-Milling-Tools-Project
python Code/flask_app.py
```

### Issue 2: "No module named 'Explainability.frequency_analysis'"

**Cause**: Old `__init__.py` trying to import non-existent modules

**Solution**: Already fixed! The `__init__.py` has been updated.

### Issue 3: Import works in test but not in Flask app

**Cause**: Different working directory

**Solution**: The flask_app.py now handles this automatically with fallback imports.

---

## Manual Fix (If Needed)

If you still have issues, you can manually ensure the import works:

### Option 1: Add to flask_app.py

At the very top of `Code/flask_app.py`, add:

```python
import sys
import os

# Ensure Code directory is in path
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)
```

### Option 2: Set PYTHONPATH

Before running the app:

**Windows (PowerShell)**:
```powershell
$env:PYTHONPATH = "Code"
python Code/flask_app.py
```

**Linux/Mac**:
```bash
export PYTHONPATH=Code
python Code/flask_app.py
```

### Option 3: Run from Code directory

```bash
cd Code
python flask_app.py
```

---

## Verification Checklist

- [ ] `test_explainability_import.py` passes
- [ ] Flask app shows `[INFO] Explainability module loaded successfully`
- [ ] Running demo shows explanation section in results
- [ ] No import errors in console

---

## Still Not Working?

### Check File Contents

Make sure `Code/Explainability/__init__.py` contains:

```python
"""
Explainability module for milling forces analysis.
"""

try:
    from .simple_explainer import (
        analyze_prediction_simple,
        format_explanation_text,
        create_contribution_breakdown_simple,
        visualize_contributions_simple
    )
    __all__ = [
        'analyze_prediction_simple',
        'format_explanation_text',
        'create_contribution_breakdown_simple',
        'visualize_contributions_simple'
    ]
except ImportError:
    __all__ = []
```

### Check Flask App Import

Make sure `Code/flask_app.py` has (around line 27):

```python
try:
    from Explainability.simple_explainer import (
        analyze_prediction_simple,
        format_explanation_text,
        create_contribution_breakdown_simple,
        visualize_contributions_simple
    )
    EXPLAINABILITY_AVAILABLE = True
    print("[INFO] Explainability module loaded successfully")
except ImportError:
    try:
        import sys
        import os
        code_dir = os.path.dirname(os.path.abspath(__file__))
        if code_dir not in sys.path:
            sys.path.insert(0, code_dir)
        
        from Explainability.simple_explainer import (
            analyze_prediction_simple,
            format_explanation_text,
            create_contribution_breakdown_simple,
            visualize_contributions_simple
        )
        EXPLAINABILITY_AVAILABLE = True
        print("[INFO] Explainability module loaded successfully (absolute path)")
    except ImportError as e:
        print(f"[WARNING] Explainability module not available: {e}")
        EXPLAINABILITY_AVAILABLE = False
```

---

## Success Indicators

When everything works, you'll see:

### In Console
```
[INFO] Explainability module loaded successfully
 * Running on http://127.0.0.1:5000
```

### In Browser (after running demo)
- Prediction section shows "Reliability: High/Medium/Low"
- "Explanation" section with key indicators
- "Recommendation" box
- "Contribution Breakdown" with bars

---

## Contact

If you're still having issues after trying all these steps, check:
1. Python version (should be 3.7+)
2. All files are saved
3. No typos in file names
4. File permissions are correct

The test script (`test_explainability_import.py`) should help identify the exact issue.
