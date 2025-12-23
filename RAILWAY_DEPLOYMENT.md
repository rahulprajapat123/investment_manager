# Railway Deployment Guide

This guide covers deploying the Investment Portfolio Manager to Railway.

## Why Railway?

- ✅ Simple deployment from GitHub
- ✅ Auto-detects Python and Node.js
- ✅ Free $5 monthly credit (no credit card required)
- ✅ Automatic HTTPS and custom domains
- ✅ Better monorepo support than alternatives
- ✅ Easy environment variables management

## Prerequisites

- GitHub account with repository pushed
- Railway account (sign up at [railway.app](https://railway.app))

---

## Fixed Configuration Files

The following files have been configured to fix deployment issues:

1. **nixpacks.toml** - Proper Python and pip setup
2. **Procfile** - Web server configuration
3. **runtime.txt** - Python version specification
4. **.dockerignore** - Exclude unnecessary files from build
5. **requirements.txt** - All necessary dependencies including werkzeug

---

## Deployment Steps

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **"Login"** or **"Start a New Project"**
3. Sign in with your GitHub account

### Step 2: Deploy Backend API

1. **Create New Project**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**
   - Choose **`investment_manager`** repository
   - Railway will auto-detect it's a Python app using Nixpacks

2. **Configure Backend**
   - Service will be created automatically
   - Railway detects `requirements.txt`, `nixpacks.toml`, and `Procfile`
   - The configuration uses Python 3.11 with Gunicorn

3. **Add Environment Variables** (Optional)
   - Click on your service
   - Go to **"Variables"** tab
   - Add any needed variables:
     ```
     PYTHON_VERSION=3.11
     FLASK_ENV=production
     ```

4. **Generate Domain**
   - Go to **"Settings"** tab
   - Under **"Networking"** → Click **"Generate Domain"**
   - Note the URL (e.g., `https://investment-manager-production.up.railway.app`)
   - This is your `BACKEND_URL` for the frontend

5. **Deploy**
   - Railway automatically deploys on push
   - Check **"Deployments"** tab for status
   - Wait 2-5 minutes for first deployment
   - Monitor build logs for any errors

### Step 3: Deploy Frontend

**Option A: Separate Service (Recommended)**

1. **Add Frontend Service**
   - In your Railway project, click **"New"**
   - Select **"GitHub Repo"** → Same repository
   - Railway creates a new service

2. **Configure Root Directory**
   - Click the frontend service
   - Go to **"Settings"** → **"Service"**
   - Set **Root Directory**: `frontend`
   - Railway will auto-detect Node.js/Vite

3. **Add Environment Variables**
   - Go to **"Variables"** tab
   - Add:
     ```
     VITE_API_URL=https://your-backend-url.up.railway.app
     NODE_VERSION=18
     ```

4. **Update Build Settings** (if needed)
   - Go to **"Settings"** → **"Deploy"**
   - Build Command: `npm install && npm run build`
   - Start Command: `npm run preview -- --host 0.0.0.0 --port $PORT`

5. **Generate Domain**
   - **"Settings"** → **"Networking"** → **"Generate Domain"**
   - This is your frontend URL

**Option B: Static Deployment**

If you prefer serving the built frontend statically:

1. Build locally: `cd frontend && npm run build`
2. Deploy the `dist` folder to a CDN/Static host
3. Set `VITE_API_URL` during build to point to Railway backend

---

## Post-Deployment

### 1. Test Backend Health
```bash
curl https://your-backend-url.up.railway.app/api/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "Portfolio Analytics API",
  "version": "1.0.0"
}
```

### 2. Test Frontend

Visit your frontend URL and:
- Upload a test Excel file
- Check if it communicates with backend
- Generate a report

### 3. Configure CORS (if needed)

If you get CORS errors, update `flask_backend.py`:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-frontend.up.railway.app",
            "http://localhost:3000"  # for local development
        ]
    }
})
```

Commit and push changes - Railway auto-deploys.

---

## Important Notes

### Free Tier

- **$5 monthly credit** (≈ 500 hours of usage)
- Services don't sleep (unlike Render free tier)
- Better for testing and small projects
- No persistent disk on free tier

### Storage Limitations

⚠️ **No persistent disk storage on free tier**:
- Uploaded files exist during service runtime
- Files are lost on redeploy or restart
- For production, consider:
  - Upgrade to paid plan with volumes
  - Use cloud storage (AWS S3, Cloudflare R2)
  - Store reports in database

### Auto-Deployment

- Railway automatically deploys on `git push`
- Each service watches the repository
- Can configure specific branches in settings

### Environment Variables

Best practices:
- Use **"Shared Variables"** for values needed by multiple services
- Use **"Service Variables"** for service-specific config
- Reference other services: `${{SERVICE_NAME.RAILWAY_PUBLIC_DOMAIN}}`

---

## Common Issues & Solutions

### Build Fails

**Python dependencies error:**
```bash
# Check requirements.txt is in root
# Verify Python version compatibility
```

**Node/npm error:**
```bash
# Ensure package.json and package-lock.json exist
# Check Node version (18 or 20 recommended)
```

### Runtime Issues

**App crashes on startup:**
- Check logs in Railway dashboard
- Verify `PORT` environment variable usage
- Check start command in railway.json

**Import errors:**
- Ensure all dependencies in requirements.txt
- Check Python path configuration

**File upload fails:**
- Verify directory creation in code
- Check file size limits (Railway has generous limits)

### Connection Issues

**Frontend can't reach backend:**
- Verify `VITE_API_URL` is set correctly
- Check CORS configuration
- Ensure backend domain is generated

**504 Gateway Timeout:**
- Increase gunicorn timeout in railway.json
- Check for long-running operations
- Consider background job processing

---

## Monitoring & Logs

### View Logs

1. Click on your service
2. Go to **"Deployments"** tab
3. Click on latest deployment
4. View real-time logs

### Metrics

- Railway dashboard shows:
  - CPU usage
  - Memory usage
  - Network traffic
  - Response times

---

## Cost Optimization

### Free Tier Tips

- Monitor usage in dashboard
- $5 credit ≈ 500 hours uptime
- Turn off services when not needed
- Use for development/testing

### Paid Plan ($5/month per service)

Benefits:
- Persistent volumes (1GB free, $0.25/GB extra)
- Priority support
- No usage limits
- Custom domains with SSL

---

## Upgrade to Production

### 1. Add Database (Optional)

```bash
# Add PostgreSQL
Railway Project → New → Database → PostgreSQL
```

Update backend to use database:
```python
# Use DATABASE_URL environment variable
```

### 2. Add Persistent Storage

```bash
# In service settings
Settings → Volumes → Add Volume
Mount path: /app/data
```

Update code to use mounted volume:
```python
DATA_DIR = Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH", ".")) / "data"
```

### 3. Add Redis (for caching)

```bash
Railway Project → New → Database → Redis
```

### 4. Set up Custom Domain

```bash
Settings → Networking → Custom Domain
Add your domain: portfolio.yourdomain.com
```

---

## CI/CD Pipeline

Railway automatically handles CI/CD:

1. **Push to GitHub**
2. **Railway detects change**
3. **Builds new image**
4. **Deploys automatically**
5. **Zero-downtime deployment**

### Configure Deployment Branches

```bash
Settings → Source → Configure branches
# Choose main, staging, or other branches
```

---

## Alternative: Deploy Entire Project

If you want both services in one:

1. Create custom Dockerfile:

```dockerfile
# Multi-stage build
FROM python:3.11-slim as backend
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

FROM node:18-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY --from=backend /app .
COPY --from=frontend /app/frontend/dist ./frontend/dist
CMD ["gunicorn", "flask_backend:app", "--bind", "0.0.0.0:$PORT"]
```

2. Update Flask to serve frontend:

```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and (Path("frontend/dist") / path).exists():
        return send_from_directory('frontend/dist', path)
    return send_from_directory('frontend/dist', 'index.html')
```

---

## Troubleshooting Common Errors

### Error: "pip: command not found"
**Fixed!** This was caused by an incomplete nixpacks configuration. The new `nixpacks.toml` properly initializes Python and pip.

**Solution Applied:**
- Updated [nixpacks.toml](nixpacks.toml) with proper Python setup
- Added `python -m pip` command to ensure pip is available
- Created [Procfile](Procfile) and [runtime.txt](runtime.txt) for better compatibility

### Error: "Usage of undefined variable '$NIXPACKS_PATH'"
**Fixed!** This error no longer occurs with the simplified nixpacks configuration.

### Error: "Build process failed"
**Checklist:**
- Ensure all files are committed and pushed to GitHub
- Check Railway build logs for specific errors
- Verify `requirements.txt` has all dependencies
- Make sure Python version matches (3.11)

### Error: "Application failed to respond"
**Solutions:**
- Check that Flask app binds to `0.0.0.0:$PORT` (already configured)
- Verify environment variables are set correctly
- Check Railway logs for runtime errors
- Ensure directories (`data/`, `reports/`, `temp_uploads/`) are created on startup

### Error: "Module not found"
**Solutions:**
- Verify all imports in `flask_backend.py` are correct
- Check that `src/` directory is properly added to Python path
- Ensure all required packages are in `requirements.txt`

---

## Support & Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Discord**: [Railway Community](https://discord.gg/railway)
- **Status**: [status.railway.app](https://status.railway.app)
- **GitHub Issues**: For application-specific problems

---

## Quick Reference

### Backend Configuration
```json
{
  "Runtime": "Python 3.11",
  "Start": "gunicorn flask_backend:app",
  "Port": "$PORT (auto-assigned)"
}
```

### Frontend Configuration
```json
{
  "Runtime": "Node 18",
  "Root": "frontend",
  "Build": "npm install && npm run build",
  "Start": "npm run preview",
  "Env": "VITE_API_URL=<backend-url>"
}
```

---

## Summary

✅ Push code to GitHub  
✅ Connect Railway to repository  
✅ Deploy backend (auto-detected)  
✅ Generate backend domain  
✅ Deploy frontend with backend URL  
✅ Test and monitor  

**Total time: ~10 minutes** ⚡

Railway makes deployment simple with automatic detection and one-click setup!
