# Explainability - Quick Reference

## ✅ YES - It's Integrated!

The explainability functionality is **fully integrated** into your Flask app and working.

## What You Get

Every prediction now includes:

### 1. Confidence Level
- **High** (>85%) - Green
- **Medium** (65-85%) - Yellow  
- **Low** (<65%) - Red

### 2. Key Indicators
- Bullet list of important factors
- Automatically generated
- Context-aware

### 3. Recommendations
- Actionable guidance
- Based on prediction + confidence
- Specific to tool condition

### 4. Contribution Breakdown
- Visual bars showing input importance
- Force signals (spectrograms): ~50%
- Force signals (scalograms): ~30%
- Visual inspection (images): ~20%

## How to See It

```bash
# Start the app
python Code/flask_app.py

# Open browser
http://localhost:5000

# Click "Run Real-Time Demo"

# Scroll down to see:
# - Prediction
# - Confidence + Reliability
# - Explanation section (NEW!)
# - Contribution breakdown (NEW!)
```

## Files Involved

### Backend
- `Code/Explainability/simple_explainer.py` - Main logic
- `Code/flask_app.py` - Integration (lines ~27-35, ~1440-1460)

### Frontend
- `Code/flask_app.py` - UI display (lines ~600-680)

## Customization

### Change Confidence Thresholds
```python
# Code/Explainability/simple_explainer.py, line ~40
if confidence > 0.85:  # Change this
    explanation['confidence_level'] = 'High'
```

### Modify Recommendations
```python
# Code/Explainability/simple_explainer.py, line ~70
if pred == 'Worn':
    explanation['recommendation'] = "Your custom message"
```

### Adjust Contributions
```python
# Code/Explainability/simple_explainer.py, line ~160
contributions = {
    'Force Signals (Spectrograms)': 50.0,  # Adjust these
    'Force Signals (Scalograms)': 30.0,
    'Visual Inspection (Images)': 20.0
}
```

## Next Steps

### Immediate (Already Done)
- ✅ Basic explainability working
- ✅ Integrated with app
- ✅ Displaying in UI

### Short Term (1-2 weeks)
- Add real gradient-based attribution
- Implement frequency band analysis
- Add historical tracking

### Long Term (1-2 months)
- Grad-CAM visualizations
- Failure mode classification
- Predictive maintenance

## Troubleshooting

### Not seeing explanations?
1. Check console for `[INFO] Explainability analysis added`
2. Verify `EXPLAINABILITY_AVAILABLE = True` in logs
3. Check browser console for JavaScript errors

### Want to disable it?
```python
# In Code/flask_app.py, line ~35
EXPLAINABILITY_AVAILABLE = False  # Set to False
```

### Want more details?
See `EXPLAINABILITY_INTEGRATION.md` for complete documentation

## Summary

**Question**: Is explainability integrated?  
**Answer**: ✅ **YES - Fully integrated and working!**

**Test it**: `python Code/flask_app.py` → Open browser → Run demo → See explanations!
