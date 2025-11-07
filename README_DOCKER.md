# 🐳 Docker Deployment - Milling Tool Wear Monitor

A simplified, production-ready Docker deployment for the Milling Tool Wear Monitoring System.

---

## 🎯 What This Does

This application analyzes real milling force data to predict tool wear using:
- Signal processing (spectrograms & scalograms)
- Deep learning (CNN model)
- Real manufacturing images
- Interactive web interface

---

## ⚡ Quick Start

### Windows (PowerShell)
```powershell
.\deploy.ps1
```

### Linux/Mac
```bash
docker-compose up -d
```

Then open: **http://localhost:5000**

---

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **4GB RAM** available
- **Port 5000** free
- **5GB disk space** for images

---

## 🚀 Deployment Steps

### 1. Clone or Download Project
```bash
git clone <your-repo>
cd Nonastrada-Milling-Tools-Project
```

### 2. Build Docker Image
```bash
docker-compose build
```
*First build takes 5-10 minutes*

### 3. Start Application
```bash
docker-compose up -d
```

### 4. Verify Running
```bash
docker-compose ps
```
Should show:
```
NAME                COMMAND                  STATUS
app                 "python /app/Code/..."   Up
```

### 5. Access Application
Open browser: **http://localhost:5000**

---

## 🎮 Using the Application

1. Click **"Run Real-Time Demo"**
2. Wait 10-30 seconds for processing
3. View results:
   - ✅ 3 Spectrograms (frequency analysis)
   - ✅ 3 Scalograms (wavelet analysis)  
   - ✅ Tool wear prediction
   - ✅ Confidence scores
   - ✅ Real manufacturing images

---

## 🛠️ Management Commands

```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Check status
docker-compose ps

# Rebuild after changes
docker-compose build --no-cache
docker-compose up -d

# Remove everything
docker-compose down -v --rmi all
```

---

## 🌐 Cloud Deployment

### AWS EC2
```bash
# On EC2 instance
sudo yum install docker -y
sudo service docker start
git clone <repo>
cd Nonastrada-Milling-Tools-Project
docker-compose up -d
```

### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/milling-monitor
gcloud run deploy --image gcr.io/PROJECT-ID/milling-monitor --port 5000
```

### Heroku
```bash
heroku container:push web
heroku container:release web
```

**See `DOCKER_DEPLOYMENT_GUIDE.md` for detailed cloud instructions**

---

## 🔧 Configuration

### Change Port
Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use port 8080 instead
```

### Environment Variables
```yaml
environment:
  - FLASK_ENV=production
  - UPLOAD_FOLDER=/app/uploads
```

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

---

## 📊 Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│     Flask App (Container)       │
│  ┌──────────────────────────┐  │
│  │  1. Extract MAT Data     │  │
│  │  2. Load Real Images     │  │
│  │  3. Generate TF Maps     │  │
│  │  4. Run CNN Model        │  │
│  │  5. Return Predictions   │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

---

## 📁 Project Structure

```
Nonastrada-Milling-Tools-Project/
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Service orchestration
├── deploy.ps1                    # Windows deployment script
├── Code/
│   ├── flask_app.py             # Main web application
│   ├── Preprocessing_Pipeline.py # Signal processing
│   └── sample_raw_force_data.py # Data extraction
├── Files/
│   ├── forces_xyz_raw.mat       # Real milling data
│   ├── vgg16_optimized_model_*.pth # Trained model
│   └── work/, tool/, chip/      # Manufacturing images
└── uploads/                      # Generated outputs
```

---

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs app

# Common fixes:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use
```bash
# Find what's using port 5000
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/Mac

# Change port in docker-compose.yml
ports:
  - "8080:5000"
```

### Out of memory
```bash
# Increase Docker memory in Docker Desktop:
# Settings → Resources → Memory → 4GB+
```

### Files not found
```bash
# Verify files exist
docker-compose exec app ls -la /app/Files
docker-compose exec app ls -la /app/Code

# If missing, rebuild
docker-compose build --no-cache
```

---

## 🔒 Production Checklist

- [ ] Use Gunicorn instead of Flask dev server
- [ ] Add Nginx reverse proxy
- [ ] Configure SSL/HTTPS
- [ ] Set up health checks
- [ ] Configure resource limits
- [ ] Enable logging/monitoring
- [ ] Set up backups
- [ ] Configure firewall rules

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Container Size | ~2.5GB |
| Startup Time | 10-20s |
| Memory Usage | 1-2GB |
| CPU Usage | 1-2 cores |
| Demo Processing | 10-30s |

---

## ✅ What's Included

✅ Flask web application  
✅ Real milling force data (512 samples)  
✅ Pre-trained CNN model  
✅ Signal processing pipeline  
✅ Spectrogram generation  
✅ Scalogram generation  
✅ Manufacturing images  
✅ Interactive web UI  

---

## ❌ What's Removed

❌ Kafka streaming (simplified for easier deployment)  
❌ Zookeeper service  
❌ Consumer service  
❌ Message queue complexity  

*The app now processes data directly in Flask - perfect for demos and production!*

---

## 📚 Documentation

- `QUICK_START_SIMPLE.md` - 3-step quick start
- `DOCKER_DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- `DEPLOYMENT_SUMMARY.md` - Changes summary
- `PROJECT_STRUCTURE.md` - Project overview

---

## 🎯 Success Indicators

✅ `docker-compose ps` shows "Up"  
✅ http://localhost:5000 loads  
✅ Demo button works  
✅ Images generate successfully  
✅ Predictions display correctly  

---

## 💡 Tips

- First build takes longer (downloads Python, PyTorch, etc.)
- Subsequent builds are faster (uses cache)
- Use `--no-cache` flag to force fresh build
- Mount `uploads/` volume to persist generated images
- Check logs if something doesn't work

---

## 🚀 Ready to Deploy!

```bash
# One command to rule them all
docker-compose up -d && echo "🎉 Running at http://localhost:5000"
```

---

**Need help?** Check the logs: `docker-compose logs -f`

**Questions?** See `DOCKER_DEPLOYMENT_GUIDE.md` for detailed instructions.

**Happy monitoring!** 🏭✨
