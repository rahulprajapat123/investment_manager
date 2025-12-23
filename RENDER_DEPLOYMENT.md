# Deployment Guide for Render

This guide will help you deploy the Investment Portfolio Manager to Render.

## Prerequisites

- GitHub account with the repository pushed
- Render account (free tier available)

## Deployment Options

### Option 1: Using Render Blueprint (Recommended)

This will deploy both backend and frontend together:

1. **Connect Your Repository**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your GitHub account if not already connected
   - Select the `investment_manager` repository

2. **Configure the Blueprint**
   - Render will automatically detect the `render.yaml` file
   - Review the two services:
     - `investment-manager-api` (Python/Flask backend)
     - `investment-manager-frontend` (Node.js/React frontend)

3. **Set Environment Variables**
   - For the frontend service, add:
     - `VITE_API_URL`: Set to your backend URL (e.g., `https://investment-manager-api.onrender.com`)

4. **Deploy**
   - Click "Apply" to deploy both services
   - Wait for the build and deployment to complete (5-10 minutes)

### Option 2: Manual Deployment (Backend Only)

If you want to deploy just the backend:

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your repository

2. **Configure Service**
   - **Name**: `investment-manager-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn flask_backend:app --bind 0.0.0.0:$PORT --workers 2`
   - **Plan**: Free

3. **Environment Variables** (Optional)
   - `PYTHON_VERSION`: 3.11.0
   - `FLASK_ENV`: production

4. **Deploy**
   - Click "Create Web Service"

### Option 3: Manual Deployment (Frontend Only)

If you want to deploy just the frontend:

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New" → "Static Site" (or Web Service for preview mode)
   - Connect your repository

2. **Configure Service**
   - **Name**: `investment-manager-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `frontend/dist` (for Static Site)
   - OR **Start Command**: `npm run preview -- --host 0.0.0.0 --port $PORT` (for Web Service)

3. **Environment Variables**
   - `VITE_API_URL`: Your backend API URL

4. **Deploy**
   - Click "Create Static Site" or "Create Web Service"

## Important Notes

### Free Tier Limitations

- Services spin down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- Limited to 750 hours per month (shared across all services)

### Data Persistence

- Free tier has **no persistent disk storage**
- Uploaded files will be lost when service restarts
- For production, consider:
  - Upgrading to paid plan with persistent disk
  - Using cloud storage (AWS S3, Google Cloud Storage)
  - Implementing database storage for reports

### CORS Configuration

The Flask backend already has CORS enabled. If you encounter CORS issues:

1. Update `flask_backend.py`:
   ```python
   CORS(app, resources={r"/api/*": {"origins": "https://your-frontend.onrender.com"}})
   ```

### File Uploads

The application uses temporary file storage. On Render's free tier:
- Files persist during the service lifetime
- Files are lost when service spins down
- Consider implementing cloud storage for production

## Post-Deployment

1. **Test the Health Endpoint**
   - Visit: `https://your-api-url.onrender.com/api/health`
   - Should return: `{"status": "healthy", ...}`

2. **Configure Frontend**
   - Update the `VITE_API_URL` environment variable in Render dashboard
   - Redeploy frontend if needed

3. **Upload Test Data**
   - Use the Upload page to test file processing
   - Generate reports to verify functionality

## Troubleshooting

### Build Failures

- **Python Dependencies**: Check `requirements.txt` for compatibility
- **Node Dependencies**: Clear npm cache and rebuild
- **Memory Issues**: Free tier has 512MB RAM limit

### Runtime Issues

- **Port Binding**: Ensure using `$PORT` environment variable
- **Timeouts**: Increase worker timeout in Procfile if needed
- **Import Errors**: Verify all dependencies are in requirements.txt

### Logs

Access logs in Render Dashboard:
- Select your service
- Click "Logs" tab
- Monitor for errors during startup and runtime

## Alternative: Deploy Separately

If Blueprint deployment fails, deploy services separately:

1. Deploy backend first (Option 2)
2. Note the backend URL
3. Deploy frontend with backend URL as VITE_API_URL (Option 3)

## Upgrade Considerations

For production use, consider:

1. **Paid Plan** ($7/month per service)
   - Persistent disk storage
   - No spin-down
   - More RAM and CPU

2. **Database Integration**
   - Add PostgreSQL for user data
   - Store report metadata in DB

3. **Cloud Storage**
   - Integrate AWS S3 or Google Cloud Storage
   - Store uploaded files and reports

4. **CDN**
   - Use Render's CDN for static frontend
   - Faster global delivery

## Support

For issues:
- Check [Render Documentation](https://render.com/docs)
- Review application logs in Render Dashboard
- Check GitHub Issues for common problems
