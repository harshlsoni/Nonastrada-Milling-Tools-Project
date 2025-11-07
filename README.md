# 🏭 Milling Tool Wear Monitoring System

A real-time manufacturing intelligence system that analyzes milling force data to predict tool wear using machine learning.

---

## 🚀 Quick Start

### Deploy with Docker (Recommended)

```powershell
# Windows
.\deploy.ps1
```

```bash
# Linux/Mac
docker-compose up -d
```

Then open: **http://localhost:5000**

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **QUICK_START_SIMPLE.md** | 3-step deployment guide |
| **README_DOCKER.md** | Complete Docker reference |
| **DOCKER_DEPLOYMENT_GUIDE.md** | Cloud deployment options |
| **DEPLOYMENT_CHECKLIST.md** | Verification steps |
| **DOCUMENTATION_INDEX.md** | Navigate all documentation |

---

## ✨ Features

- ✅ Real-time milling force data analysis
- ✅ Spectrogram generation (X, Y, Z axes)
- ✅ Scalogram generation (wavelet analysis)
- ✅ CNN-based tool wear prediction
- ✅ Interactive web interface
- ✅ Real manufacturing images
- ✅ Confidence scores and visualization

---

## 🏗️ Architecture

```
Browser → Flask App → Signal Processing → CNN Model → Predictions
```

**Single container deployment** - No Kafka complexity, production-ready.

---

## 📊 What It Does

1. **Extracts** real milling force data (~98K samples per axis)
2. **Generates** spectrograms and scalograms for frequency analysis
3. **Processes** through CNN model for tool wear classification
4. **Displays** results with confidence scores (Sharp/Used/Worn)

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **ML:** PyTorch, CNN (VGG16-based)
- **Signal Processing:** SciPy, PyWavelets
- **Deployment:** Docker
- **Data:** Real milling force sensor data

---

## 📁 Project Structure

```
Nonastrada-Milling-Tools-Project/
├── Code/
│   ├── flask_app.py                 # Main web application
│   ├── Preprocessing_Pipeline.py    # Signal processing
│   ├── sample_raw_force_data.py     # Data extraction
│   └── Model_Files/                 # ML model architecture
├── Files/
│   ├── forces_xyz_raw.mat           # Real milling data (512 samples)
│   ├── vgg16_optimized_model_*.pth  # Trained CNN model
│   └── work/, tool/, chip/          # Manufacturing images
├── docker-compose.yml               # Docker orchestration
├── Dockerfile                       # Container definition
├── deploy.ps1                       # Automated deployment
└── Documentation/                   # Comprehensive guides
```

---

## 🎯 Use Cases

- **Predictive Maintenance:** Predict tool wear before failure
- **Quality Control:** Monitor manufacturing process quality
- **Research:** Study milling force patterns and tool degradation
- **Education:** Learn about signal processing and ML in manufacturing

---

## 🌐 Deployment Options

- **Local:** Docker Compose
- **AWS:** EC2, ECS
- **Google Cloud:** Cloud Run
- **Azure:** Container Instances
- **Heroku:** Container deployment
- **DigitalOcean:** App Platform

See **DOCKER_DEPLOYMENT_GUIDE.md** for detailed instructions.

---

## 📈 Performance

- **Startup Time:** 10-20 seconds
- **Memory Usage:** 2-4GB
- **Processing Time:** 10-30 seconds per sample
- **Container Size:** ~2.5GB

---

## 🔧 Requirements

- Docker Desktop
- 4GB RAM minimum
- 5GB disk space
- Port 5000 available

---

## 🎓 Getting Started

1. **Read:** `QUICK_START_SIMPLE.md`
2. **Deploy:** Run `.\deploy.ps1`
3. **Test:** Open http://localhost:5000
4. **Explore:** Click "Run Real-Time Demo"

---

## 📞 Support

- **Quick Start:** See `QUICK_START_SIMPLE.md`
- **Troubleshooting:** See `README_DOCKER.md`
- **Cloud Deploy:** See `DOCKER_DEPLOYMENT_GUIDE.md`
- **All Docs:** See `DOCUMENTATION_INDEX.md`

---

## ✅ What's Included

✅ Real milling force data (512 datapoints)  
✅ Pre-trained CNN model  
✅ Signal processing pipeline  
✅ Interactive web UI  
✅ Manufacturing images  
✅ Comprehensive documentation  
✅ Automated deployment scripts  

---

## 🎉 Ready to Deploy!

```bash
docker-compose up -d
```

**Access at:** http://localhost:5000

---

**Built for manufacturing intelligence and predictive maintenance.** 🏭✨
