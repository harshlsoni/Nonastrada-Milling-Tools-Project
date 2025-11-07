# 🚀 Quick Start Guide (Simplified - No Kafka)

## Run in 3 Steps

### Step 1: Build the Docker Image
```bash
docker-compose build
```

### Step 2: Start the Application
```bash
docker-compose up -d
```

### Step 3: Open Your Browser
Navigate to: **http://localhost:5000**

---

## 🎯 Using the Application

1. Click **"Run Real-Time Demo"** button
2. Wait 10-30 seconds for processing
3. View results:
   - 3 Spectrograms (frequency analysis)
   - 3 Scalograms (wavelet analysis)
   - Tool wear prediction (Sharp/Used/Worn)
   - Confidence scores

---

## 🛑 Stop the Application

```bash
docker-compose down
```

---

## 🔍 Check Status

```bash
# View logs
docker-compose logs -f

# Check if running
docker-compose ps
```

---

## 🐛 Troubleshooting

### Port 5000 already in use?
```bash
# Stop the container
docker-compose down

# Edit docker-compose.yml and change:
ports:
  - "8080:5000"  # Use port 8080 instead

# Restart
docker-compose up -d

# Access at http://localhost:8080
```

### Application not responding?
```bash
# Restart
docker-compose restart

# Or rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 What's Included

- ✅ Flask web application
- ✅ Real milling force data (512 samples)
- ✅ Pre-trained CNN model
- ✅ Signal processing pipeline
- ✅ Image generation (spectrograms/scalograms)
- ❌ Kafka streaming (removed for simplicity)

---

## 🌐 Deploy to Cloud

See **DOCKER_DEPLOYMENT_GUIDE.md** for detailed cloud deployment instructions:
- AWS EC2
- Google Cloud Run
- Azure Container Instances
- Heroku
- DigitalOcean

---

That's it! Your milling tool monitoring system is ready to use. 🎉
