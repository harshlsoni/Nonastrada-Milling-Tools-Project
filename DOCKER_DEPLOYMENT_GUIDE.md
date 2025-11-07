# 🐳 Docker Deployment Guide

## Quick Start (Simplified - No Kafka)

This guide shows how to build and deploy the Milling Tool Wear Monitoring system using Docker.

---

## 📋 Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)
- At least 4GB RAM available
- Ports 5000 available

---

## 🚀 Local Deployment

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and start the application
docker-compose up -d

# Check if it's running
docker-compose ps

# View logs
docker-compose logs -f app

# Stop the application
docker-compose down
```

Access the application at: **http://localhost:5000**

### Option 2: Using Docker Directly

```bash
# Build the image
docker build -t milling-tool-monitor .

# Run the container
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  --name milling-app \
  milling-tool-monitor

# Check if it's running
docker ps

# View logs
docker logs -f milling-app

# Stop the container
docker stop milling-app
docker rm milling-app
```

Access the application at: **http://localhost:5000**

---

## 🌐 Cloud Deployment Options

### 1. AWS EC2 Deployment

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Install Docker (Amazon Linux 2)
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone your repository
git clone <your-repo-url>
cd Nonastrada-Milling-Tools-Project

# Build and run
docker-compose up -d

# Configure security group to allow port 5000
```

Access at: **http://your-ec2-ip:5000**

### 2. AWS ECS (Elastic Container Service)

```bash
# Build and tag image
docker build -t milling-tool-monitor .
docker tag milling-tool-monitor:latest <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/milling-tool-monitor:latest

# Push to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com
docker push <your-aws-account-id>.dkr.ecr.<region>.amazonaws.com/milling-tool-monitor:latest

# Create ECS task definition and service via AWS Console or CLI
```

### 3. Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/<project-id>/milling-tool-monitor

# Deploy to Cloud Run
gcloud run deploy milling-tool-monitor \
  --image gcr.io/<project-id>/milling-tool-monitor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 5000 \
  --memory 2Gi
```

### 4. Azure Container Instances

```bash
# Build and push to Azure Container Registry
az acr build --registry <registry-name> --image milling-tool-monitor .

# Deploy to ACI
az container create \
  --resource-group <resource-group> \
  --name milling-tool-monitor \
  --image <registry-name>.azurecr.io/milling-tool-monitor:latest \
  --dns-name-label milling-tool-monitor \
  --ports 5000
```

### 5. DigitalOcean App Platform

```bash
# Push to Docker Hub
docker build -t <your-dockerhub-username>/milling-tool-monitor .
docker push <your-dockerhub-username>/milling-tool-monitor

# Deploy via DigitalOcean Console:
# 1. Create new App
# 2. Select Docker Hub as source
# 3. Enter image: <your-dockerhub-username>/milling-tool-monitor
# 4. Set HTTP port: 5000
# 5. Deploy
```

### 6. Heroku

```bash
# Login to Heroku
heroku login
heroku container:login

# Create app
heroku create milling-tool-monitor

# Build and push
heroku container:push web -a milling-tool-monitor
heroku container:release web -a milling-tool-monitor

# Open app
heroku open -a milling-tool-monitor
```

---

## 🔧 Configuration

### Environment Variables

You can customize the application using environment variables:

```bash
# In docker-compose.yml
environment:
  - FLASK_ENV=production
  - UPLOAD_FOLDER=/app/uploads
  - PORT=5000
```

### Volume Mounts

The `uploads` directory is mounted to persist generated images:

```yaml
volumes:
  - ./uploads:/app/uploads
```

---

## 📊 Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 core | 2 cores |
| RAM | 2GB | 4GB |
| Storage | 5GB | 10GB |
| Network | 1Mbps | 10Mbps |

---

## 🔍 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Port 5000 already in use
docker-compose down
# Change port in docker-compose.yml: "8080:5000"

# 2. Out of memory
# Increase Docker memory limit in Docker Desktop settings
```

### Application errors

```bash
# Enter container for debugging
docker-compose exec app /bin/bash

# Check Python environment
python --version
pip list

# Test Flask manually
cd /app/Code
python flask_app.py
```

### Files not found

```bash
# Verify files are copied
docker-compose exec app ls -la /app/Files
docker-compose exec app ls -la /app/Code

# Rebuild if needed
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔒 Production Best Practices

### 1. Use Production WSGI Server

Update Dockerfile CMD:

```dockerfile
# Install gunicorn
RUN pip install gunicorn

# Use gunicorn instead of Flask dev server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "Code.flask_app:app"]
```

### 2. Add Health Checks

```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. Set Resource Limits

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### 4. Use Nginx Reverse Proxy

```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - app
```

---

## 📦 Building for Different Architectures

```bash
# For ARM64 (Apple Silicon, Raspberry Pi)
docker buildx build --platform linux/arm64 -t milling-tool-monitor:arm64 .

# For AMD64 (Most servers)
docker buildx build --platform linux/amd64 -t milling-tool-monitor:amd64 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t milling-tool-monitor:latest .
```

---

## 🎯 Quick Commands Reference

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Remove everything
docker-compose down -v --rmi all

# Update and restart
git pull
docker-compose build
docker-compose up -d
```

---

## 🌟 Success Indicators

✅ Container status shows "Up"  
✅ Application accessible at http://localhost:5000  
✅ "Run Real-Time Demo" button works  
✅ Spectrograms and scalograms generate successfully  
✅ Model predictions display with confidence scores  

---

## 📞 Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Verify files exist: `docker-compose exec app ls -la /app/Files`
3. Test locally first: `python Code/flask_app.py`
4. Rebuild from scratch: `docker-compose build --no-cache`
