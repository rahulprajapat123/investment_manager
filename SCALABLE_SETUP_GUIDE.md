# 🚀 Scalable Stack Setup Guide

## Overview
This guide will help you set up Supabase (PostgreSQL) + Upstash Redis + RQ for handling 1000+ clients.

**Total Setup Time:** 30-60 minutes  
**Cost:** $0 (FREE tier for both services)

---

## 📋 Prerequisites

- Python 3.11+
- Git
- Web browser

---

## Step 1: Create Supabase Account (5 minutes)

### 1.1 Sign up for Supabase

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email
4. FREE tier: Unlimited API requests, 500MB database

### 1.2 Create a New Project

1. Click "New Project"
2. Choose an organization (create one if needed)
3. Fill in details:
   - **Name:** `portfolio-analytics` (or your choice)
   - **Database Password:** Create a strong password (save it!)
   - **Region:** Choose closest to you
4. Click "Create new project" (takes 2-3 minutes)

### 1.3 Get API Credentials

1. Once project is ready, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: https://xxx.supabase.co)
   - **anon/public key** (long string starting with `eyJ...`)

### 1.4 Create Database Tables

1. Go to **SQL Editor** (left sidebar)
2. Click "New query"
3. Copy the entire content from `database_schema.sql` file
4. Paste it into the SQL editor
5. Click "Run" (green play button)
6. You should see "Success. No rows returned"

✅ **Supabase is ready!**

---

## Step 2: Create Upstash Redis Account (5 minutes)

### 2.1 Sign up for Upstash

1. Go to https://upstash.com
2. Click "Get Started"
3. Sign up with GitHub (recommended) or email
4. FREE tier: 10,000 commands/day, 256MB storage

### 2.2 Create a Redis Database

1. Click "Create Database"
2. Fill in details:
   - **Name:** `portfolio-cache`
   - **Type:** Regional (cheaper, good for most cases)
   - **Region:** Choose closest to you
3. Click "Create"

### 2.3 Get Redis URL

1. Click on your database name
2. Scroll to "REST API" section
3. Copy the **UPSTASH_REDIS_REST_URL**
   - Format: `https://xxx.upstash.io`
4. Also note the **Token** if using REST API

✅ **Upstash Redis is ready!**

---

## Step 3: Configure Your Project (10 minutes)

### 3.1 Install New Dependencies

```bash
cd "C:\Users\praja\Desktop\demo investment project"
. .\venv311\Scripts\Activate.ps1
pip install supabase redis rq python-dotenv
```

### 3.2 Create .env File

```bash
# Copy the example file
copy .env.example .env

# Edit .env file with your credentials
notepad .env
```

Fill in your credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# Upstash Redis Configuration  
UPSTASH_REDIS_URL=redis://default:your-password@your-endpoint.upstash.io:6379

# Enable database mode
USE_DATABASE=true

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
```

**How to get Redis URL:**
1. In Upstash dashboard, go to your database
2. Scroll to **Redis Connect** section
3. Copy the URL that starts with `redis://`

### 3.3 Test Database Connection

```bash
python -c "from src.database import init_supabase; client = init_supabase(); print('✅ Connected!' if client else '❌ Failed')"
```

### 3.4 Test Redis Connection

```bash
python -c "from redis import Redis; import os; from dotenv import load_dotenv; load_dotenv(); r = Redis.from_url(os.getenv('UPSTASH_REDIS_URL')); r.ping(); print('✅ Redis Connected!')"
```

✅ **Project configured!**

---

## Step 4: Running the Application (Dual Mode)

### Mode 1: File-Based (Current - No Setup Needed)

Set in `.env`:
```env
USE_DATABASE=false
```

Run normally:
```bash
python flask_backend.py
```

### Mode 2: Database Mode (Scalable)

Set in `.env`:
```env
USE_DATABASE=true
```

**Terminal 1 - Backend:**
```bash
cd "C:\Users\praja\Desktop\demo investment project"
. .\venv311\Scripts\Activate.ps1
python flask_backend.py
```

**Terminal 2 - RQ Worker:**
```bash
cd "C:\Users\praja\Desktop\demo investment project"
. .\venv311\Scripts\Activate.ps1
python src/worker.py
```

**Terminal 3 - Frontend:**
```bash
cd "C:\Users\praja\Desktop\demo investment project\frontend"
npm run dev
```

✅ **Application running in scalable mode!**

---

## Step 5: Verify Everything Works (5 minutes)

### 5.1 Check Backend

Open: http://localhost:5000/
You should see: `{"status": "healthy", ...}`

### 5.2 Check Frontend

Open: http://localhost:3000/
Upload a file and generate a report.

### 5.3 Check Database

1. Go to Supabase → **Table Editor**
2. You should see data in:
   - `clients` table
   - `trades` table
   - `capital_gains` table
   - `job_queue` table

### 5.4 Check Redis

In Upstash dashboard → **Data Browser**
You should see job entries.

---

## 🎯 What You Get

### Before (File-Based)
- ✅ Works for 1-100 clients
- ⚠️ Slow for 100+ clients
- ⚠️ No concurrent processing
- ⚠️ Limited querying

### After (Database Mode)
- ✅ Handles 1000+ clients easily
- ✅ Fast queries with indexes
- ✅ Background job processing
- ✅ Real-time status updates
- ✅ Advanced filtering & search
- ✅ Data persistence & backups
- ✅ FREE up to reasonable scale

---

## 📊 Monitoring & Management

### Supabase Dashboard
- **Database:** View/edit tables
- **Auth:** User management (future)
- **Storage:** File uploads (future)
- **Logs:** Query performance
- **Reports:** Database insights

### Upstash Dashboard
- **Data Browser:** View cached data
- **Stats:** Command count, hit rate
- **Logs:** Redis operations

---

## 🔄 Switching Between Modes

You can easily switch between file-based and database modes:

**Use Files (Current):**
```env
USE_DATABASE=false
```
- Good for: Development, testing, <100 clients
- No setup needed
- Data stored in `data/` folder

**Use Database (Scalable):**
```env
USE_DATABASE=true
```
- Good for: Production, 100+ clients
- Requires Supabase + Upstash setup
- Data stored in cloud database

---

## ⚠️ Troubleshooting

### "Connection refused" error
- Check if Redis URL is correct
- Verify Upstash database is active
- Try restarting Redis in Upstash dashboard

### "Table does not exist"
- Make sure you ran the SQL schema in Supabase
- Check **Table Editor** to verify tables exist

### Jobs not processing
- Make sure RQ worker is running (`python src/worker.py`)
- Check worker terminal for errors
- Verify Redis connection

### "Module not found" errors
```bash
pip install supabase redis rq python-dotenv
```

---

## 💰 Cost Breakdown

### FREE Tier (Perfect for 100-500 clients)

**Supabase:**
- Database: 500MB
- API requests: Unlimited
- Storage: 1GB
- **Cost: $0/month**

**Upstash Redis:**
- Commands: 10,000/day (300K/month)
- Storage: 256MB
- **Cost: $0/month**

**Total: $0/month** ✨

### If You Exceed Free Tier

**Supabase Pro:**
- Database: 8GB
- Everything unlimited
- **Cost: $25/month**

**Upstash:**
- Commands: 1M/day
- Storage: 1GB
- **Cost: ~$10/month**

**Total: $35/month for 2000+ clients**

---

## 🚀 Next Steps

1. ✅ Test in development mode first
2. ✅ Upload sample data and verify in Supabase
3. ✅ Monitor free tier usage
4. ✅ Deploy to Vercel/Railway when ready
5. ✅ Add authentication if needed
6. ✅ Implement advanced features (search, filters, etc.)

---

## 📞 Support

- **Supabase Docs:** https://supabase.com/docs
- **Upstash Docs:** https://docs.upstash.com
- **RQ Docs:** https://python-rq.org

---

## ✅ Quick Reference

```bash
# Start backend
python flask_backend.py

# Start RQ worker (only in database mode)
python src/worker.py

# Start frontend
cd frontend && npm run dev

# Test database
python -c "from src.database import init_supabase; init_supabase()"

# Test Redis
python -c "from redis import Redis; r = Redis.from_url('your-url'); r.ping()"
```

---

**You're all set! 🎉**

The system is now ready to scale to 1000+ clients with NO COST!
