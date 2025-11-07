# 🚀 Deploy to Render.com

Complete guide to deploy your Milling Tool Monitor to Render.com.

---

## ✅ Prerequisites

- GitHub account with your code pushed
- Render.com account (free - sign up at https://render.com)

---

## 📋 Quick Deployment Steps

### Step 1: Push to GitHub

Make sure these files are in your repository:
```
✓ Dockerfile
✓ render.yaml
✓ requirements.txt
✓ Code/
✓ Files/
```

```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

---

### Step 2: Connect to Render

1. Go to https://render.com
2. Click **"Get Started"** or **"Sign Up"**
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

---

### Step 3: Create Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Find your repository in the list
4. Click **"Connect"**

---

### Step 4: Configure Service

Render will auto-detect your `render.yaml` file. Verify these settings:

**Basic Settings:**
- **Name:** `milling-tool-monitor` (or your choice)
- **Environment:** `Docker`
- **Region:** Choose closest to you (Oregon, Frankfurt, Singapore, etc.)
- **Branch:** `main` (or your default branch)

**Plan:**
- **Free** - Good for demos/testing
  - 750 hours/month
  - Sleeps after 15 min inactivity
  - 512 MB RAM
  
- **Starter ($7/mo)** - Recommended for production
  - Always on
  - 512 MB RAM
  - Better performance

**Environment Variables** (auto-configured from render.yaml):
- `FLASK_ENV=production`
- `UPLOAD_FOLDER=/app/uploads`
- `PORT=5000`

---

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes first time)
3. Watch the build logs

**Build Process:**
```
Building Docker image...
Installing dependencies...
Copying files...
Starting application...
✓ Deploy successful!
```

---

### Step 6: Access Your App

Once deployed, you'll get a URL like:
```
https://milling-tool-monitor.onrender.com
```

Click the URL to access your application!

---

## 🎯 What Happens During Deployment

1. **Build Phase** (~5-10 min first time)
   - Pulls Python 3.11 base image
   - Installs system dependencies
   - Installs Python packages (PyTorch, Flask, etc.)
   - Copies your code and data files
   - Creates Docker image

2. **Deploy Phase** (~30 sec)
   - Starts container
   - Runs Flask application
   - Health check on `/`
   - Service goes live

3. **Subsequent Deploys** (~2-3 min)
   - Uses cached layers
   - Much faster

---

## 🔧 Configuration Details

### render.yaml Explained

```yaml
services:
  - type: web                    # Web service type
    name: milling-tool-monitor   # Your app name
    env: docker                  # Use Docker
    plan: free                   # Free tier (or 'starter')
    region: oregon               # Server location
    healthCheckPath: /           # Health check endpoint
    envVars:                     # Environment variables
      - key: FLASK_ENV
        value: production
      - key: UPLOAD_FOLDER
        value: /app/uploads
      - key: PORT
        value: 5000
    disk:                        # Persistent storage
      name: uploads
      mountPath: /app/uploads
      sizeGB: 1                  # 1GB for generated images
```

---

## 📊 Free Tier Limitations

### What's Included:
- ✅ 750 hours/month (enough for demos)
- ✅ 512 MB RAM
- ✅ 1 GB persistent disk
- ✅ Custom domain support
- ✅ Auto-deploy from GitHub
- ✅ Free SSL certificate

### Limitations:
- ⏰ Sleeps after 15 min of inactivity
- ⏳ ~30 sec wake-up time on first request
- 🐌 Slower performance than paid tiers

### When to Upgrade to Starter ($7/mo):
- Need always-on service
- Want faster performance
- Production use
- No sleep/wake delays

---

## 🔄 Auto-Deploy from GitHub

Render automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Render automatically:
# 1. Detects push
# 2. Rebuilds Docker image
# 3. Deploys new version
# 4. Zero-downtime deployment
```

---

## 🌐 Custom Domain (Optional)

### Add Your Domain:

1. Go to your service dashboard
2. Click **"Settings"**
3. Scroll to **"Custom Domain"**
4. Click **"Add Custom Domain"**
5. Enter your domain: `milling.yourdomain.com`
6. Add CNAME record to your DNS:
   ```
   CNAME milling -> milling-tool-monitor.onrender.com
   ```
7. Wait for DNS propagation (~5-60 min)
8. Free SSL certificate auto-generated

---

## 📈 Monitoring

### View Logs:
1. Go to service dashboard
2. Click **"Logs"** tab
3. See real-time application logs

### View Metrics:
1. Click **"Metrics"** tab
2. See:
   - CPU usage
   - Memory usage
   - Request count
   - Response times

### Set Up Alerts:
1. Click **"Settings"**
2. Scroll to **"Notifications"**
3. Add email or Slack webhook
4. Get notified of:
   - Deploy failures
   - Service crashes
   - High resource usage

---

## 🐛 Troubleshooting

### Build Fails

**Check build logs:**
```
Click "Logs" → "Build Logs"
```

**Common issues:**
- Missing files in repo
- Dockerfile syntax error
- Dependency conflicts

**Fix:**
```bash
# Test locally first
docker build -t test .
docker run -p 5000:5000 test

# If works locally, push to GitHub
git push origin main
```

---

### Service Won't Start

**Check deploy logs:**
```
Click "Logs" → "Deploy Logs"
```

**Common issues:**
- Port not configured correctly
- Missing environment variables
- Files not found

**Fix:**
- Verify `PORT` environment variable
- Check file paths in code
- Ensure Files/ directory is in repo

---

### App Sleeps (Free Tier)

**Symptom:** First request takes 30+ seconds

**This is normal on free tier!**

**Solutions:**
1. **Upgrade to Starter** ($7/mo) - no sleep
2. **Use a ping service** - Keep app awake
   - https://uptimerobot.com (free)
   - Ping your URL every 5 minutes
3. **Accept the delay** - Fine for demos

---

### Out of Memory

**Symptom:** Service crashes during processing

**Solutions:**
1. **Upgrade plan** - Get more RAM
2. **Optimize code** - Reduce memory usage
3. **Process smaller batches** - Split large datasets

---

## 💰 Cost Breakdown

### Free Tier
- **Cost:** $0/month
- **Hours:** 750/month
- **RAM:** 512 MB
- **Storage:** 1 GB
- **Best for:** Demos, testing, personal projects

### Starter Tier
- **Cost:** $7/month
- **Hours:** Unlimited
- **RAM:** 512 MB
- **Storage:** 1 GB
- **Best for:** Production, always-on services

### Standard Tier
- **Cost:** $25/month
- **Hours:** Unlimited
- **RAM:** 2 GB
- **Storage:** 10 GB
- **Best for:** High-traffic production apps

---

## 🔒 Security

### Automatic Features:
- ✅ Free SSL/HTTPS certificate
- ✅ DDoS protection
- ✅ Automatic security updates
- ✅ Isolated containers

### Best Practices:
- Use environment variables for secrets
- Don't commit sensitive data
- Enable 2FA on Render account
- Regularly update dependencies

---

## 📚 Additional Resources

- **Render Docs:** https://render.com/docs
- **Docker Docs:** https://docs.render.com/docker
- **Support:** https://render.com/support

---

## ✅ Deployment Checklist

Before deploying:
- [ ] Code pushed to GitHub
- [ ] `render.yaml` in repository root
- [ ] `Dockerfile` tested locally
- [ ] `Files/` directory included
- [ ] Environment variables configured
- [ ] Render account created
- [ ] Repository connected to Render

After deploying:
- [ ] Build completed successfully
- [ ] Service is running
- [ ] URL is accessible
- [ ] Demo button works
- [ ] Images generate correctly
- [ ] No errors in logs

---

## 🎉 Success!

Your Milling Tool Monitor is now live on Render!

**Your URL:** `https://milling-tool-monitor.onrender.com`

**Next Steps:**
1. Test all features
2. Share the URL
3. Monitor logs and metrics
4. Consider upgrading if needed

---

## 🆘 Need Help?

1. **Check logs** - Most issues show up here
2. **Test locally** - Verify Docker works on your machine
3. **Render docs** - https://render.com/docs
4. **Community** - https://community.render.com

---

**Happy deploying!** 🚀
