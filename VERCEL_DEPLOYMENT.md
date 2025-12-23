# Vercel Deployment Guide

## Quick Deploy to Vercel

### Option 1: Using Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from root directory:**
   ```bash
   vercel
   ```

4. **Set Environment Variable:**
   When prompted or in Vercel dashboard, set:
   ```
   VITE_API_URL=https://your-railway-backend-url.up.railway.app
   ```

### Option 2: Using Vercel Dashboard

1. **Import Project:**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Vercel will auto-detect the configuration from `vercel.json`

2. **Configure Build Settings:**
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

3. **Set Environment Variables:**
   - Go to Project Settings → Environment Variables
   - Add: `VITE_API_URL` = `https://your-railway-backend-url.up.railway.app`

4. **Deploy:**
   - Click "Deploy"
   - Wait for deployment to complete

### Option 3: Using vercel.json (Root Level)

The `vercel.json` in the root is already configured for monorepo deployment.

Just run:
```bash
vercel --prod
```

## Environment Variables Required

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | Your Railway backend URL | Backend API endpoint |

## Important Notes

1. **CORS Configuration:** Ensure your Flask backend on Railway has CORS enabled for your Vercel domain
2. **API URL Format:** Use `https://` (not `http://`) for production
3. **No trailing slash:** Don't add `/` at the end of `VITE_API_URL`

## Vercel Build Settings Summary

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "cd frontend && npm install"
}
```

## Troubleshooting

### Build Failed
- Check that all dependencies are in `frontend/package.json`
- Verify Node.js version compatibility (18.x recommended)

### API Calls Failing
- Verify `VITE_API_URL` is set correctly in Vercel environment variables
- Check Railway backend CORS settings
- Ensure Railway backend is running and accessible

### 404 Errors on Refresh
- Vercel should automatically handle SPA routing
- If issues persist, add `vercel.json` in frontend directory with rewrites

## Testing Deployment

After deployment, test these endpoints:
1. Visit your Vercel URL
2. Check if dashboard loads
3. Try uploading a file
4. Verify API calls work with Railway backend
