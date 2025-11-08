# Milling Tool Wear Monitoring System

An intelligent manufacturing system that analyzes milling force data to predict tool wear using deep learning and signal processing.

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-ghostfreak538%2Fnonastrada__project-blue?logo=docker)](https://hub.docker.com/r/ghostfreak538/nonastrada_project)
[![Docker Image](https://img.shields.io/badge/docker%20pull-ghostfreak538%2Fnonastrada__project-blue)](https://hub.docker.com/r/ghostfreak538/nonastrada_project)

---

## Quick Start

### Deploy with Docker (Recommended)

**Option 1: Use Pre-built Image from Docker Hub**

```bash
# Pull and run the image
docker pull ghostfreak538/nonastrada_project:latest
mkdir uploads
docker run -d -p 5000:5000 -v %cd%/uploads:/app/uploads --restart unless-stopped --name milling-monitor ghostfreak538/nonastrada_project:latest

# Or use docker-compose
docker-compose up -d
```

**Option 2: Build Locally**

```powershell
# Windows
.\deploy.ps1
```

```bash
# Linux/Mac
docker-compose up -d --build
```

Then open: **http://localhost:5000**

### Run Locally (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python Code/flask_app.py
```

Access at: **http://localhost:5000**

---

## Features

### Core Capabilities
- **Real-time Analysis**: Process milling force data from 512 real manufacturing samples
- **Multi-Modal CNN**: VGG16-based model using 9 input modalities
- **Signal Processing**: Automated spectrogram and scalogram generation
- **Tool Wear Classification**: Predicts Sharp, Used, or Worn tool states
- **Professional UI**: Clean interface with real-time progress tracking

### New Features (Latest Updates)
- **Explainability**: Understand why predictions are made
  - Confidence levels (High/Medium/Low)
  - Key indicators and recommendations
  - Contribution breakdown by input type
- **Progress Tracking**: Real-time visual feedback during processing
- **Image Validation**: Ensures predictions use real manufacturing data
- **Custom Data Testing**: Test with your own milling data

---

## What It Does

1. **Extracts** real milling force data (X, Y, Z axes, ~20K-98K samples)
2. **Generates** time-frequency representations:
   - Spectrograms (frequency-time analysis)
   - Scalograms (wavelet analysis)
3. **Processes** through multi-modal CNN:
   - 3 Spectrograms + 3 Scalograms + 3 Images (Work, Tool, Chip)
4. **Predicts** tool condition with confidence scores
5. **Explains** the reasoning behind predictions

---

## Architecture

```
Input Data
    ├─ Force Signals (X, Y, Z) → Spectrograms
    ├─ Force Signals (X, Y, Z) → Scalograms  
    └─ Images (Work, Tool, Chip)
                ↓
        VGG16 Multi-Modal CNN
                ↓
    Prediction + Explainability
                ↓
        Web Interface
```

**Tech Stack:**
- Backend: Flask (Python)
- ML: PyTorch, VGG16-based CNN
- Signal Processing: SciPy, PyWavelets
- Deployment: Docker
- Data: Real milling force sensor data (512 samples)

---

## Project Structure

```
Nonastrada-Milling-Tools-Project/
├── Code/
│   ├── flask_app.py                    # Main web application
│   ├── Preprocessing_Pipeline.py       # Signal processing
│   ├── sample_raw_force_data.py        # Data extraction
│   ├── Explainability/                 # NEW: Explainability module
│   │   ├── simple_explainer.py         # Prediction explanations
│   │   └── modality_attribution.py     # Feature importance
│   └── Model_Files/                    # ML model architecture
│       └── network_architecture/       # VGG16, ResNet, etc.
├── Files/
│   ├── forces_xyz_raw.mat              # Real milling data (512 samples)
│   ├── labels.csv                      # Image ID mappings
│   ├── vgg16_optimized_model_*.pth     # Trained CNN model
│   └── work/, tool/, chip/             # Manufacturing images (512 each)
├── custom_data/                        # NEW: Test data folder
│   ├── create_sample_data.py           # Generate test data
│   ├── test_custom_data.py             # Test pipeline
│   └── sample_test_*/                  # Sample test cases
├── docker-compose.yml                  # Docker orchestration
├── Dockerfile                          # Container definition
├── requirements.txt                    # Python dependencies
└── Documentation/                      # See below
```

---

## Documentation

### Getting Started
- **README.md** (this file) - Overview and quick start
- **QUICK_START_SIMPLE.md** - 3-step deployment guide
- **DOCUMENTATION_INDEX.md** - Navigate all documentation

### Deployment
- **README_DOCKER.md** - Complete Docker reference
- **DOCKER_DEPLOYMENT_GUIDE.md** - Cloud deployment options
- **DEPLOYMENT_CHECKLIST.md** - Verification steps
- **RENDER_DEPLOYMENT.md** - Render.com deployment
- **RENDER_QUICK_START.md** - Quick Render setup

### Features & Updates
- **EXPLAINABILITY_INTEGRATION.md** - How explainability works
- **EXPLAINABILITY_PLAN.md** - Complete roadmap (9 features)
- **EXPLAINABILITY_SUMMARY.md** - Quick overview
- **CUSTOM_DATA_SUMMARY.md** - Using custom test data
- **IMAGE_VALIDATION_FIX.md** - Data integrity improvements
- **PROGRESS_BAR_FIX_V2.md** - Progress tracking details

### Quick References
- **QUICK_REFERENCE.md** - Common commands and tips
- **EXPLAINABILITY_QUICK_REF.md** - Explainability features
- **EXPLAINABILITY_TROUBLESHOOTING.md** - Fix common issues

---

## Key Features Explained

### 1. Explainability (NEW)

Every prediction now includes:

**Confidence Level**
- High (>85%) - Green indicator
- Medium (65-85%) - Yellow indicator
- Low (<65%) - Red indicator

**Key Indicators**
- Bullet list of important factors
- Automatically generated
- Context-aware

**Recommendations**
- Actionable guidance based on prediction
- Specific to tool condition
- Confidence-adjusted

**Contribution Breakdown**
- Shows which inputs influenced the prediction
- Visual bars for easy understanding
- Typical: Force signals 50%, Wavelets 30%, Images 20%

### 2. Custom Data Testing (NEW)

Test the pipeline with your own data:

```bash
# Generate sample test data
python custom_data/create_sample_data.py --multiple

# Test with custom data
python custom_data/test_custom_data.py --all
```

See `custom_data/README.md` for data format requirements.

### 3. Progress Tracking (IMPROVED)

Real-time visual feedback:
- Smooth progress bar animation
- Step-by-step status updates
- Professional logging (no emojis)
- Syncs with backend processing

### 4. Data Validation (NEW)

Ensures prediction quality:
- Validates real manufacturing images exist
- Rejects predictions with synthetic data
- Clear error messages
- Maintains data integrity

---

## Use Cases

- **Predictive Maintenance**: Predict tool wear before failure
- **Quality Control**: Monitor manufacturing process quality
- **Process Optimization**: Understand which factors affect tool life
- **Research**: Study milling force patterns and tool degradation
- **Education**: Learn about signal processing and ML in manufacturing
- **Custom Testing**: Validate with your own milling data

---

## Performance

- **Startup Time**: 10-20 seconds
- **Memory Usage**: 2-4GB
- **Processing Time**: 10-30 seconds per sample
- **Container Size**: ~2.5GB
- **Dataset**: 512 real manufacturing samples
- **Model**: VGG16-based multi-modal CNN

---

## Requirements

### For Docker Deployment
- Docker Desktop
- 4GB RAM minimum
- 5GB disk space
- Port 5000 available

### For Local Development
- Python 3.7+
- PyTorch
- SciPy, PyWavelets
- Flask
- 4GB RAM minimum

---

## Getting Started

### 1. Quick Demo
```bash
# Deploy with Docker
docker-compose up -d

# Open browser
http://localhost:5000

# Click "Run Real-Time Demo"
```

### 2. Custom Data
```bash
# Generate test data
python custom_data/create_sample_data.py --multiple

# Test the pipeline
python custom_data/test_custom_data.py --all
```

### 3. Explore Features
- View spectrograms and scalograms
- See prediction explanations
- Check contribution breakdowns
- Test with different samples

---

## What's New (Latest Updates)

### Explainability Module
- ✅ Confidence levels with color coding
- ✅ Key indicators for each prediction
- ✅ Actionable recommendations
- ✅ Contribution breakdown visualization
- ✅ Natural language explanations

### Usability Improvements
- ✅ Professional progress tracking
- ✅ Real-time status updates
- ✅ Clean logging (no emojis)
- ✅ Smooth progress animations

### Data Integrity
- ✅ Image validation before predictions
- ✅ labels.csv mapping (512 datapoints)
- ✅ Clear error messages
- ✅ Prevents invalid predictions

### Testing Framework
- ✅ Custom data folder structure
- ✅ Sample data generation scripts
- ✅ Test data validation
- ✅ 3 pre-generated test cases

---

## Deployment Options

### Docker Hub
Pre-built image available: **`ghostfreak538/nonastrada_project:latest`**

```bash
docker pull ghostfreak538/nonastrada_project:latest
docker run -d -p 5000:5000 ghostfreak538/nonastrada_project:latest
```

### Cloud Platforms
- **AWS**: EC2, ECS, Elastic Beanstalk
- **Google Cloud**: Cloud Run, Compute Engine
- **Azure**: Container Instances, App Service
- **Heroku**: Container deployment
- **DigitalOcean**: App Platform
- **Render**: Web Service (see RENDER_DEPLOYMENT.md)

### Local
- **Docker Compose**: `docker-compose up -d`
- **Python**: `python Code/flask_app.py`

---

## API Endpoints

### Main Endpoints
- `GET /` - Web interface
- `POST /predict` - Upload custom data for prediction
- `GET /demo` - Run demo with real data
- `GET /progress/<session_id>` - Get processing progress
- `GET /images/<path>` - Serve generated visualizations

### Response Format
```json
{
  "prediction_interpretation": {
    "predicted_label": "Worn",
    "confidence": 0.87,
    "explanation": {
      "confidence_level": "High",
      "key_indicators": ["Strong indicators of tool wear detected"],
      "recommendation": "High confidence worn tool detected. Recommend immediate tool replacement."
    },
    "contributions": {
      "Force Signals (Spectrograms)": 50.0,
      "Force Signals (Scalograms)": 30.0,
      "Visual Inspection (Images)": 20.0
    }
  }
}
```

---

## Troubleshooting

### Common Issues

**"Explainability module not available"**
- Run: `python test_explainability_import.py`
- See: `EXPLAINABILITY_TROUBLESHOOTING.md`

**Progress bar not syncing**
- This is normal - uses hybrid simulation + polling
- See: `PROGRESS_BAR_FIX_V2.md`

**Missing images error**
- Check `Files/labels.csv` exists
- Run: `python generate_labels.py`
- Run: `python check_images.py`

**Docker issues**
- See: `README_DOCKER.md`
- Check: `DEPLOYMENT_CHECKLIST.md`

---

## Development

### Project Status
- ✅ Core functionality complete
- ✅ Explainability integrated
- ✅ Custom data testing ready
- ✅ Docker deployment working
- ✅ Documentation comprehensive

### Future Enhancements
See `EXPLAINABILITY_PLAN.md` for roadmap:
- Grad-CAM visualizations
- Historical trend tracking
- Failure mode classification
- Advanced attribution methods
- Predictive maintenance scheduling

---

## Support & Documentation

### Quick Help
- **Quick Start**: `QUICK_START_SIMPLE.md`
- **Docker Help**: `README_DOCKER.md`
- **All Docs**: `DOCUMENTATION_INDEX.md`

### Feature-Specific
- **Explainability**: `EXPLAINABILITY_INTEGRATION.md`
- **Custom Data**: `custom_data/README.md`
- **Troubleshooting**: `EXPLAINABILITY_TROUBLESHOOTING.md`

### Reference
- **Commands**: `QUICK_REFERENCE.md`
- **API**: See "API Endpoints" section above
- **Architecture**: `PROJECT_STRUCTURE.md`

---

## What's Included

✅ Real milling force data (512 datapoints)  
✅ Pre-trained VGG16 multi-modal CNN  
✅ Signal processing pipeline (spectrograms + scalograms)  
✅ Interactive web UI with progress tracking  
✅ Manufacturing images (work, tool, chip)  
✅ Explainability module (NEW)  
✅ Custom data testing framework (NEW)  
✅ Comprehensive documentation (27 files)  
✅ Automated deployment scripts  
✅ Docker containerization  

---

## License & Credits

Built for manufacturing intelligence and predictive maintenance.

**Dataset**: Real milling force sensor data  
**Model**: VGG16-based multi-modal CNN  
**Framework**: PyTorch, Flask, Docker  

---

## Ready to Deploy!

### Quick Start with Docker Hub

```bash
# Pull and run the pre-built image
docker pull ghostfreak538/nonastrada_project:latest
docker run -d -p 5000:5000 -v $(pwd)/uploads:/app/uploads ghostfreak538/nonastrada_project:latest
```

### Or use Docker Compose

```bash
docker-compose up -d
```

### Or run locally

```bash
python Code/flask_app.py
```

**Access at**: http://localhost:5000

**Click "Run Real-Time Demo"** to see it in action!

---

**Manufacturing Intelligence • Predictive Maintenance • Deep Learning**

