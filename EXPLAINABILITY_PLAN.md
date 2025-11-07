# Explainability Implementation Plan for Milling Forces Analysis

## Project Understanding

### Current System
- **Model**: VGG16-based multi-modal CNN
- **Input Modalities** (9 total):
  - 3 Spectrograms (X, Y, Z axes)
  - 3 Scalograms (X, Y, Z axes)
  - 3 Images (Work, Tool, Chip)
- **Task**: Tool wear classification (3 classes: Sharp, Used, Worn)
- **Architecture**: Feature extraction → Fusion → Classification
- **Current Output**: Class prediction + confidence scores

### Gap Analysis
Currently, users see:
- ✅ Prediction (e.g., "Worn Tool")
- ✅ Confidence (e.g., "87%")
- ✅ Spectrograms and scalograms

Missing:
- ❌ **Why** this prediction was made
- ❌ **Which** features influenced the decision
- ❌ **How** confident we should be
- ❌ **What** to do about it

---

## Recommended Explainability Features

### Priority 1: Quick Wins (1-2 days each)

#### 1. Feature Importance by Modality ⭐⭐⭐
**What**: Show which input modalities contributed most to the prediction

**Implementation**:
```python
def get_modality_contributions(model, x_dict, target_class):
    """Calculate contribution of each modality using gradient-based attribution."""
    contributions = {}
    
    for modality_name, modality_input in x_dict.items():
        # Enable gradients
        modality_input.requires_grad = True
        
        # Forward pass
        output = model(x_dict)
        
        # Backward pass for target class
        model.zero_grad()
        output[0, target_class].backward(retain_graph=True)
        
        # Calculate contribution (gradient magnitude)
        contribution = modality_input.grad.abs().mean().item()
        contributions[modality_name] = contribution
    
    # Normalize to percentages
    total = sum(contributions.values())
    contributions = {k: (v/total)*100 for k, v in contributions.items()}
    
    return contributions
```

**UI Display**:
```
Prediction Breakdown:
├─ Force Signals (Spectrograms): 45%
│  ├─ X-axis: 18%
│  ├─ Y-axis: 15%
│  └─ Z-axis: 12%
├─ Force Signals (Scalograms): 30%
│  ├─ X-axis: 12%
│  ├─ Y-axis: 10%
│  └─ Z-axis: 8%
└─ Visual Inspection: 25%
   ├─ Tool image: 15%
   ├─ Chip image: 7%
   └─ Work image: 3%
```

**Value**: Operators understand which sensors/images matter most

---

#### 2. Frequency Band Analysis ⭐⭐⭐
**What**: Identify which frequency ranges indicate tool wear

**Implementation**:
```python
def analyze_frequency_bands(spectrogram, frequencies):
    """Identify dominant frequency bands and their significance."""
    # Define frequency bands
    bands = {
        'Low (0-100 Hz)': (0, 100),
        'Medium (100-500 Hz)': (100, 500),
        'High (500-2000 Hz)': (500, 2000),
        'Very High (2000+ Hz)': (2000, 5000)
    }
    
    band_energies = {}
    for band_name, (f_min, f_max) in bands.items():
        # Find indices for this frequency range
        idx = (frequencies >= f_min) & (frequencies <= f_max)
        
        # Calculate energy in this band
        energy = np.mean(spectrogram[idx, :])
        band_energies[band_name] = energy
    
    return band_energies

def interpret_frequency_patterns(band_energies, axis_name):
    """Generate human-readable interpretation."""
    interpretations = []
    
    if band_energies['High (500-2000 Hz)'] > threshold_high:
        interpretations.append(
            f"Elevated vibrations at 500-2000 Hz in {axis_name}-axis "
            f"(typical of bearing wear or tool chatter)"
        )
    
    if band_energies['Low (0-100 Hz)'] > threshold_low:
        interpretations.append(
            f"Increased low-frequency forces in {axis_name}-axis "
            f"(indicates tool dulling or material buildup)"
        )
    
    return interpretations
```

**UI Display**:
```
Frequency Analysis:
X-Axis:
  ⚠ High energy at 250-350 Hz (bearing wear indicator)
  ✓ Normal low-frequency pattern

Y-Axis:
  ⚠ Elevated 500-800 Hz (tool chatter detected)
  ⚠ Increasing amplitude over time

Z-Axis:
  ✓ Stable frequency distribution
  ℹ Peak at 150 Hz (normal cutting frequency)
```

**Value**: Connects signal patterns to physical phenomena

---

#### 3. Confidence Calibration & Uncertainty ⭐⭐
**What**: Show how reliable the prediction is

**Implementation**:
```python
def calculate_prediction_uncertainty(model, x_dict, n_samples=10):
    """Estimate prediction uncertainty using MC Dropout."""
    model.train()  # Enable dropout
    
    predictions = []
    for _ in range(n_samples):
        with torch.no_grad():
            output = model(x_dict)
            probs = torch.softmax(output, dim=1)
            predictions.append(probs.cpu().numpy())
    
    predictions = np.array(predictions)
    
    # Calculate statistics
    mean_probs = predictions.mean(axis=0)
    std_probs = predictions.std(axis=0)
    
    # Entropy as uncertainty measure
    entropy = -np.sum(mean_probs * np.log(mean_probs + 1e-10))
    
    return {
        'mean_probabilities': mean_probs,
        'std_probabilities': std_probs,
        'uncertainty': entropy,
        'confidence_interval': (mean_probs - 2*std_probs, mean_probs + 2*std_probs)
    }
```

**UI Display**:
```
Prediction: Worn Tool
Confidence: 87% ± 5%
Reliability: High

Confidence Breakdown:
  Sharp:  5% (±2%)  ▁
  Used:   8% (±3%)  ▂
  Worn:  87% (±5%)  ████████▊

Recommendation: High confidence - proceed with tool replacement
```

**Value**: Users know when to trust predictions

---

### Priority 2: Medium Effort (3-5 days each)

#### 4. Grad-CAM Visualization ⭐⭐⭐
**What**: Highlight which parts of images/spectrograms the model focuses on

**Implementation**:
```python
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_backward_hook(self.save_gradient)
    
    def save_activation(self, module, input, output):
        self.activations = output.detach()
    
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()
    
    def generate_cam(self, input_tensor, target_class):
        # Forward pass
        output = self.model(input_tensor)
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward()
        
        # Calculate weights
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        
        # Weighted combination
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = torch.relu(cam)
        
        # Normalize
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        
        return cam.squeeze().cpu().numpy()

def visualize_attention(original_image, cam, alpha=0.5):
    """Overlay CAM heatmap on original image."""
    import cv2
    
    # Resize CAM to match image
    cam_resized = cv2.resize(cam, (original_image.shape[1], original_image.shape[0]))
    
    # Create heatmap
    heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    
    # Overlay
    overlayed = (1 - alpha) * original_image + alpha * heatmap
    overlayed = np.uint8(overlayed)
    
    return overlayed
```

**UI Display**:
- Heatmaps overlaid on tool/chip/work images
- Highlighted regions in spectrograms
- Color-coded attention maps

**Value**: Visual explanation of model focus

---

#### 5. Historical Trend Analysis ⭐⭐
**What**: Track tool condition over time

**Implementation**:
```python
class ToolConditionTracker:
    def __init__(self, db_path='tool_history.db'):
        self.db = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                tool_id TEXT,
                prediction TEXT,
                confidence REAL,
                x_peak_freq REAL,
                y_peak_freq REAL,
                z_peak_freq REAL,
                force_amplitude REAL
            )
        ''')
    
    def log_prediction(self, tool_id, prediction_data):
        """Store prediction for historical analysis."""
        self.db.execute('''
            INSERT INTO predictions 
            (timestamp, tool_id, prediction, confidence, ...)
            VALUES (?, ?, ?, ?, ...)
        ''', (datetime.now(), tool_id, ...))
        self.db.commit()
    
    def get_degradation_curve(self, tool_id):
        """Get tool wear progression over time."""
        query = '''
            SELECT timestamp, prediction, confidence, force_amplitude
            FROM predictions
            WHERE tool_id = ?
            ORDER BY timestamp
        '''
        return pd.read_sql(query, self.db, params=(tool_id,))
    
    def predict_remaining_life(self, tool_id):
        """Estimate remaining tool life based on degradation rate."""
        history = self.get_degradation_curve(tool_id)
        
        # Fit degradation model
        # ... (linear regression or more sophisticated model)
        
        return estimated_remaining_parts
```

**UI Display**:
```
Tool Condition History (Tool #1234)

Current: Worn (87% confidence)
Previous: Used (72% confidence) - 2 hours ago
Initial: Sharp (95% confidence) - 8 hours ago

Degradation Rate: 10.8% per hour
Estimated Remaining Life: 50 parts

[Chart showing confidence over time]
```

**Value**: Predictive maintenance scheduling

---

#### 6. Counterfactual Explanations ⭐⭐
**What**: "What would need to change for a different prediction?"

**Implementation**:
```python
def generate_counterfactual(model, x_dict, current_class, target_class):
    """Find minimal changes needed to change prediction."""
    
    # Start with current input
    x_modified = {k: v.clone().requires_grad_(True) for k, v in x_dict.items()}
    
    optimizer = torch.optim.Adam([v for v in x_modified.values()], lr=0.01)
    
    for iteration in range(100):
        output = model(x_modified)
        
        # Loss: maximize target class, minimize changes
        target_loss = -output[0, target_class]
        change_loss = sum([(x_modified[k] - x_dict[k]).pow(2).sum() 
                          for k in x_dict.keys()])
        
        loss = target_loss + 0.1 * change_loss
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Check if prediction changed
        pred_class = output.argmax(dim=1).item()
        if pred_class == target_class:
            break
    
    # Calculate what changed
    changes = {}
    for k in x_dict.keys():
        diff = (x_modified[k] - x_dict[k]).abs().mean().item()
        changes[k] = diff
    
    return changes
```

**UI Display**:
```
Current Prediction: Worn Tool

To achieve "Sharp Tool" classification:
  • Reduce X-axis vibrations at 250-350 Hz by 35%
  • Decrease force amplitude by 20%
  • Improve chip color uniformity (less discoloration)

To achieve "Used Tool" classification:
  • Reduce high-frequency noise by 15%
  • Slight improvement in tool edge sharpness
```

**Value**: Actionable insights for process improvement

---

### Priority 3: Advanced Features (1-2 weeks each)

#### 7. SHAP Values for Global Explanations ⭐⭐⭐
**What**: Understand feature importance across entire dataset

**Implementation**:
```python
import shap

def calculate_shap_values(model, background_data, test_data):
    """Calculate SHAP values for model interpretability."""
    
    # Create explainer
    explainer = shap.DeepExplainer(model, background_data)
    
    # Calculate SHAP values
    shap_values = explainer.shap_values(test_data)
    
    return shap_values

def visualize_shap_summary(shap_values, feature_names):
    """Create SHAP summary plot."""
    shap.summary_plot(shap_values, feature_names=feature_names)
```

**Value**: Understand global model behavior

---

#### 8. Attention Mechanism Visualization ⭐⭐
**What**: If model uses attention, show what it attends to

**Implementation**: Requires model architecture modification to include attention layers

---

#### 9. Failure Mode Classification ⭐⭐⭐
**What**: Not just "worn", but WHY worn (flank wear, crater wear, chipping, etc.)

**Implementation**:
```python
class FailureModeClassifier:
    def __init__(self):
        self.failure_patterns = {
            'flank_wear': {
                'frequency_signature': [200, 400, 600],
                'force_increase': 'gradual',
                'chip_appearance': 'normal'
            },
            'crater_wear': {
                'frequency_signature': [150, 300],
                'force_increase': 'sudden',
                'chip_appearance': 'discolored'
            },
            'chipping': {
                'frequency_signature': [500, 1000, 1500],
                'force_increase': 'spiky',
                'chip_appearance': 'irregular'
            }
        }
    
    def classify_failure_mode(self, prediction_data):
        """Determine specific type of tool wear."""
        # Analyze frequency patterns
        # Check force characteristics
        # Examine chip appearance
        # Return most likely failure mode
        pass
```

**UI Display**:
```
Prediction: Worn Tool (87% confidence)

Failure Mode Analysis:
  Primary: Flank Wear (75% probability)
    • Gradual force increase detected
    • Characteristic frequencies: 200-600 Hz
    • Chip appearance normal
    
  Secondary: Crater Wear (20% probability)
    • Some discoloration in chips
    • Moderate frequency shift
    
Recommended Action:
  • Replace tool within next 50 parts
  • Check cutting speed (may be too high)
  • Verify coolant flow
```

**Value**: Specific, actionable maintenance guidance

---

## Implementation Roadmap

### Week 1-2: Foundation
1. Set up explainability module structure
2. Implement modality contribution analysis
3. Add frequency band analysis
4. Create basic UI components

### Week 3-4: Core Features
1. Implement Grad-CAM visualization
2. Add confidence calibration
3. Create historical tracking database
4. Build trend analysis dashboard

### Week 5-6: Advanced Features
1. Implement counterfactual explanations
2. Add SHAP value analysis
3. Create failure mode classifier
4. Integrate all features into UI

### Week 7-8: Polish & Testing
1. User testing and feedback
2. Performance optimization
3. Documentation
4. Deployment

---

## Technical Architecture

### Backend Structure
```
Code/
├── Explainability/
│   ├── __init__.py
│   ├── modality_attribution.py      # Feature importance
│   ├── frequency_analysis.py        # Frequency band analysis
│   ├── gradcam.py                   # Grad-CAM implementation
│   ├── uncertainty.py               # Confidence calibration
│   ├── counterfactual.py            # Counterfactual generation
│   ├── shap_analysis.py             # SHAP values
│   ├── failure_modes.py             # Failure classification
│   └── historical_tracker.py        # Trend analysis
├── flask_app.py                     # Add explainability endpoints
└── Preprocessing_Pipeline.py        # Add analysis hooks
```

### New API Endpoints
```python
@app.route('/explain/<session_id>')
def explain_prediction(session_id):
    """Get detailed explanation for a prediction."""
    pass

@app.route('/history/<tool_id>')
def get_tool_history(tool_id):
    """Get historical data for a tool."""
    pass

@app.route('/counterfactual/<session_id>')
def get_counterfactual(session_id):
    """Generate counterfactual explanation."""
    pass
```

### Frontend Components
```javascript
// Modality contribution chart
function renderModalityContribution(data) {
    // Bar chart showing contribution percentages
}

// Frequency analysis display
function renderFrequencyAnalysis(data) {
    // Annotated spectrograms with interpretations
}

// Confidence visualization
function renderConfidenceDisplay(data) {
    // Confidence bars with uncertainty ranges
}

// Historical trend chart
function renderTrendChart(data) {
    // Time series of tool condition
}
```

---

## Success Metrics

### Quantitative
- **User Trust**: Survey score on prediction confidence
- **Decision Time**: Time to make maintenance decision (target: <2 min)
- **False Positives**: Unnecessary tool changes (target: <10%)
- **Missed Failures**: Unexpected tool failures (target: <2%)

### Qualitative
- Users understand why predictions are made
- Operators can explain model decisions to supervisors
- Maintenance decisions are data-driven
- System is trusted for production use

---

## Quick Start Implementation

### Minimal Viable Explainability (1 day)

```python
# Add to flask_app.py

def get_simple_explanation(prediction_data):
    """Generate basic explanation for prediction."""
    
    explanation = {
        'prediction': prediction_data['predicted_label'],
        'confidence': prediction_data['confidence'],
        'key_indicators': [],
        'recommendation': ''
    }
    
    # Analyze frequency patterns
    if has_high_frequency_energy(prediction_data):
        explanation['key_indicators'].append(
            "High-frequency vibrations detected (500-800 Hz)"
        )
    
    # Analyze force amplitude
    if has_elevated_forces(prediction_data):
        explanation['key_indicators'].append(
            "Force amplitude 30% above baseline"
        )
    
    # Generate recommendation
    if explanation['prediction'] == 'Worn' and explanation['confidence'] > 0.8:
        explanation['recommendation'] = "Replace tool within next 50 parts"
    elif explanation['prediction'] == 'Used':
        explanation['recommendation'] = "Continue monitoring, check again in 100 parts"
    else:
        explanation['recommendation'] = "Tool in good condition, continue operation"
    
    return explanation
```

This gives immediate value while building toward more sophisticated features.

---

## Resources Needed

### Development
- 1 ML Engineer (explainability implementation)
- 1 Frontend Developer (UI components)
- 1 Domain Expert (interpretation validation)

### Tools & Libraries
- PyTorch (already have)
- SHAP (`pip install shap`)
- Captum (`pip install captum`) - PyTorch interpretability
- Plotly (`pip install plotly`) - Interactive visualizations
- SQLite (already available) - Historical tracking

### Time Estimate
- **Minimal**: 1-2 days
- **Core Features**: 4-6 weeks
- **Full Implementation**: 8-10 weeks

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize features** based on user needs
3. **Start with Priority 1** features (quick wins)
4. **Iterate based on feedback**
5. **Expand to advanced features** as needed

Would you like me to implement any of these features first?
