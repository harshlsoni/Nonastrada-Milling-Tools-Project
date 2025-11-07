# ⚡ Render.com Quick Start

Deploy in 5 minutes!

---

## 🚀 Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Go to Render
- Visit: https://render.com
- Sign up with GitHub
- Authorize Render

### 3. Create Web Service
- Click **"New +"** → **"Web Service"**
- Select your repository
- Click **"Connect"**

### 4. Configure (Auto-detected from render.yaml)
- **Name:** milling-tool-monitor
- **Environment:** Docker
- **Plan:** Free (or Starter $7/mo)
- Click **"Create Web Service"**

### 5. Wait & Access
- Wait 5-10 minutes for first build
- Get your URL: `https://milling-tool-monitor.onrender.com`
- Done! 🎉

---

## 📋 What's Included

✅ `render.yaml` - Render configuration  
✅ Updated `Dockerfile` - Cloud-ready  
✅ Updated `flask_app.py` - PORT support  
✅ `RENDER_DEPLOYMENT.md` - Full guide  

---

## 🎯 Free Tier

- **Cost:** $0/month
- **Hours:** 750/month
- **RAM:** 512 MB
- **Note:** Sleeps after 15 min (30s wake-up)

---

## 🔄 Auto-Deploy

Push to GitHub = Auto-deploy:
```bash
git push origin main
# Render rebuilds & deploys automatically
```

---

## 🐛 Troubleshooting

**Build fails?**
- Check logs in Render dashboard
- Test locally: `docker build -t test .`

**App won't start?**
- Verify Files/ directory is in repo
- Check environment variables

**Slow first request?**
- Normal on free tier (app sleeps)
- Upgrade to Starter ($7/mo) for always-on

---

## 📚 Full Guide

See **RENDER_DEPLOYMENT.md** for:
- Detailed instructions
- Configuration options
- Custom domains
- Monitoring
- Troubleshooting

---

## ✅ Quick Check

Before deploying:
- [ ] Code on GitHub
- [ ] render.yaml in root
- [ ] Files/ directory included
- [ ] Tested locally

---

**Your app will be live at:**
`https://milling-tool-monitor.onrender.com`

🚀 **Deploy now!**
