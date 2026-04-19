# ZenvyDesk API - Render Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ZenvyDesk API backend to Render.com with the custom domain `api.zenvydesk.site`.

**Product Description:**
ZenvyDesk is an AI-powered desktop tool for content creation and workflow assistance. This backend provides secure Facebook OAuth authentication for user login. All actions are user-initiated and user-controlled.

**Target URL:** https://api.zenvydesk.site

## Prerequisites

### 1. Render Account
- Sign up at https://render.com (free tier available)
- Verify your email address

### 2. GitHub Repository (Recommended)
- Push your code to GitHub
- Or prepare to deploy from local files

### 3. Facebook App Configuration
- Facebook App ID and Secret ready
- App configured for production (see Facebook Configuration section below)

### 4. DNS Access
- Access to DNS management for `zenvydesk.site`
- Ability to add CNAME records

## Deployment Methods

### Method 1: Deploy from GitHub (Recommended)

This is the easiest and most maintainable approach.

#### Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - ZenvyDesk API"

# Add remote and push
git remote add origin https://github.com/yourusername/zenvydesk-api.git
git branch -M main
git push -u origin main
```

#### Step 2: Connect to Render

1. Log in to https://dashboard.render.com
2. Click **"New +"** button
3. Select **"Web Service"**
4. Click **"Connect GitHub"** (if not already connected)
5. Authorize Render to access your repositories
6. Find and select your `zenvydesk-api` repository

#### Step 3: Configure Web Service

Fill in the following settings:

**Basic Settings:**
- **Name:** `zenvydesk-api`
- **Region:** Choose closest to your users (e.g., Oregon, Frankfurt)
- **Branch:** `main`
- **Root Directory:** Leave empty (or `.` if needed)
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** 
  ```
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- Select **"Free"** (or paid plan for better performance)

#### Step 4: Add Environment Variables

Click **"Advanced"** and add these environment variables:

| Key | Value |
|-----|-------|
| `APP_NAME` | `ZenvyDesk API` |
| `APP_ENV` | `production` |
| `APP_BASE_URL` | `https://api.zenvydesk.site` |
| `FRONTEND_BASE_URL` | `https://zenvydesk.site` |
| `FACEBOOK_APP_ID` | Your Facebook App ID |
| `FACEBOOK_APP_SECRET` | Your Facebook App Secret |
| `FACEBOOK_REDIRECT_URI` | `https://api.zenvydesk.site/auth/facebook/callback` |
| `FACEBOOK_SCOPES` | `public_profile,email` |
| `DATABASE_URL` | `sqlite:///./zenvydesk.db` |
| `SESSION_EXPIRY_MINUTES` | `15` |
| `SECRET_KEY` | Click "Generate" or paste your own |

**Important Notes:**
- Click **"Generate"** for `SECRET_KEY` to auto-generate a secure value
- Keep `FACEBOOK_APP_SECRET` secure - never commit to git
- Use the exact values shown above for URLs

#### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying
3. Wait for deployment to complete (2-5 minutes)
4. Watch the logs for any errors

**Expected Log Output:**
```
==> Building...
Collecting fastapi...
Successfully installed fastapi-0.109.0 ...
==> Deploying...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

#### Step 6: Test Default URL

Once deployed, Render provides a default URL like:
```
https://zenvydesk-api.onrender.com
```

Test it:
```bash
curl https://zenvydesk-api.onrender.com/health
```

**Expected Response:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

If this works, proceed to custom domain setup.

---

### Method 2: Deploy from render.yaml (Blueprint)

If you have `render.yaml` in your repository:

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will detect `render.yaml` automatically
5. Review the configuration
6. Add the required secret environment variables:
   - `FACEBOOK_APP_ID`
   - `FACEBOOK_APP_SECRET`
7. Click **"Apply"**

This method auto-configures everything from the YAML file.

---

### Method 3: Manual Upload (No Git)

If you don't want to use GitHub:

1. Create a new Web Service on Render
2. Choose **"Deploy from Git"** but use Render's Git hosting
3. Or use Render's CLI to deploy directly

**Note:** GitHub deployment is strongly recommended for easier updates.

---

## Custom Domain Setup

### Step 1: Add Custom Domain in Render

1. Go to your service dashboard
2. Click **"Settings"** tab
3. Scroll to **"Custom Domain"** section
4. Click **"Add Custom Domain"**
5. Enter: `api.zenvydesk.site`
6. Click **"Save"**

Render will show you a CNAME target like:
```
zenvydesk-api.onrender.com
```

**Copy this exact value** - you'll need it for DNS.

### Step 2: Configure DNS

Go to your DNS provider where `zenvydesk.site` is managed (e.g., Cloudflare, Namecheap, GoDaddy).

**Add a CNAME Record:**

| Type | Name | Target | TTL |
|------|------|--------|-----|
| CNAME | `api` | `zenvydesk-api.onrender.com` | Auto or 3600 |

**Important:**
- Use the exact CNAME target Render provided
- Name should be `api` (not `api.zenvydesk.site`)
- Do NOT use an A record
- Do NOT add a trailing dot unless your DNS provider requires it

**Example for Cloudflare:**
- Type: CNAME
- Name: api
- Target: zenvydesk-api.onrender.com
- Proxy status: DNS only (gray cloud)
- TTL: Auto

### Step 3: Wait for DNS Propagation

DNS changes can take 5-60 minutes to propagate.

**Check DNS propagation:**
```bash
nslookup api.zenvydesk.site
```

**Expected output:**
```
Server:  8.8.8.8
Address: 8.8.8.8#53

Non-authoritative answer:
api.zenvydesk.site    canonical name = zenvydesk-api.onrender.com
```

### Step 4: Wait for SSL Certificate

Once DNS is propagated, Render automatically provisions an SSL certificate.

This usually takes 1-5 minutes after DNS is verified.

**Check certificate status:**
- Go to Render dashboard → Settings → Custom Domain
- Status should show: **"Verified"** with a green checkmark

### Step 5: Test Custom Domain

Once SSL is ready:

```bash
curl https://api.zenvydesk.site/health
```

**Expected Response:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**Test in browser:**
```
https://api.zenvydesk.site/
```

You should see:
```json
{
  "app": "ZenvyDesk API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

## Facebook App Configuration

Before testing OAuth, configure your Facebook App:

### Required Settings

Go to https://developers.facebook.com/apps/ and select your app.

**1. App Domains**
- Settings → Basic → App Domains
- Add: `zenvydesk.site`

**2. Valid OAuth Redirect URIs**
- Products → Facebook Login → Settings
- Add: `https://api.zenvydesk.site/auth/facebook/callback`

**3. Required URLs**
- Settings → Basic
- Privacy Policy URL: `https://zenvydesk.site/privacy-policy`
- Terms of Service URL: `https://zenvydesk.site/terms-of-service`
- Data Deletion Instructions URL: `https://zenvydesk.site/data-deletion`

**4. Permissions**
- App Review → Permissions and Features
- Request: `public_profile` (default)
- Request: `email`

**5. App Mode**
- For testing: Keep in Development mode
- For production: Switch to Live mode after testing

---

## Testing the Deployment

### Test 1: Health Check

```bash
curl https://api.zenvydesk.site/health
```

**Expected:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**Status:** 200 OK

### Test 2: Root Endpoint

```bash
curl https://api.zenvydesk.site/
```

**Expected:**
```json
{
  "app":"ZenvyDesk API",
  "version":"1.0.0",
  "status":"running",
  "docs":"/docs"
}
```

### Test 3: API Documentation

Open in browser:
```
https://api.zenvydesk.site/docs
```

You should see interactive Swagger UI documentation.

### Test 4: Facebook OAuth Login

Open in browser:
```
https://api.zenvydesk.site/auth/facebook/login
```

**Expected behavior:**
1. Browser redirects to Facebook
2. URL changes to: `https://www.facebook.com/v18.0/dialog/oauth?client_id=...`
3. Facebook login page appears
4. After login, redirects back to callback URL
5. Success page displays

**If it fails**, see Troubleshooting section below.

---

## Monitoring and Logs

### View Logs

1. Go to Render dashboard
2. Select your service
3. Click **"Logs"** tab
4. View real-time logs

**Or use Render CLI:**
```bash
render logs -s zenvydesk-api
```

### Common Log Messages

**Successful startup:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting ZenvyDesk API in production mode
INFO:     Database initialized
INFO:     Application startup complete.
```

**Request logs:**
```
INFO:     127.0.0.1:12345 - "GET /health HTTP/1.1" 200 OK
```

---

## Updating the Application

### Method 1: Git Push (Automatic)

If deployed from GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push origin main
```

Render automatically detects the push and redeploys.

### Method 2: Manual Deploy

1. Go to Render dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## Troubleshooting

### Issue 1: Build Fails

**Symptoms:**
- Deployment fails during build
- Error: "Could not find a version that satisfies the requirement"

**Solutions:**
1. Check `requirements.txt` is present
2. Verify all dependencies are valid
3. Check Python version compatibility
4. View build logs for specific error

**Fix:**
```bash
# Test locally first
pip install -r requirements.txt
```

### Issue 2: Service Won't Start

**Symptoms:**
- Build succeeds but service crashes
- Error: "Application startup failed"

**Solutions:**
1. Check environment variables are set
2. Verify `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` are correct
3. Check logs for specific error
4. Ensure `PORT` environment variable is used correctly

**Debug:**
- Check Render logs for Python errors
- Verify all required env vars are set
- Test database initialization

### Issue 3: /health Returns 404

**Symptoms:**
- Service is running but `/health` returns 404

**Solutions:**
1. Verify start command is correct:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
2. Check that `app/main.py` exists
3. Verify routes are imported correctly

### Issue 4: Custom Domain Not Working

**Symptoms:**
- Default URL works but custom domain doesn't
- SSL certificate not provisioning

**Solutions:**
1. Verify DNS CNAME record is correct
2. Check DNS propagation: `nslookup api.zenvydesk.site`
3. Wait longer (DNS can take up to 1 hour)
4. Ensure CNAME points to exact Render target
5. Check Render dashboard for domain verification status

**Common DNS mistakes:**
- Using A record instead of CNAME
- Wrong CNAME target
- Cloudflare proxy enabled (should be DNS only)

### Issue 5: Facebook OAuth Fails

**Symptoms:**
- `/auth/facebook/login` doesn't redirect
- Error: "Invalid OAuth redirect URI"

**Solutions:**
1. Verify `FACEBOOK_REDIRECT_URI` env var is exactly:
   ```
   https://api.zenvydesk.site/auth/facebook/callback
   ```
2. Check Facebook App settings have the same redirect URI
3. Ensure no trailing slashes
4. Verify Facebook App ID and Secret are correct
5. Check Facebook App is in correct mode (Development/Live)

**Test environment variables:**
```bash
# In Render shell (if available)
echo $FACEBOOK_APP_ID
echo $FACEBOOK_REDIRECT_URI
```

### Issue 6: Database Resets on Redeploy

**Symptoms:**
- Users and sessions disappear after redeploy

**Cause:**
- SQLite database is stored in ephemeral filesystem
- Render resets filesystem on each deploy

**Solutions:**
1. **For MVP/Testing:** Accept data loss (SQLite is fine)
2. **For Production:** Upgrade to PostgreSQL
   - Add Render PostgreSQL database
   - Update `DATABASE_URL` to PostgreSQL connection string
   - Render provides persistent PostgreSQL storage

**Upgrade to PostgreSQL:**
1. In Render dashboard, create new PostgreSQL database
2. Copy the Internal Database URL
3. Update `DATABASE_URL` environment variable
4. Redeploy service

---

## Environment Variables Reference

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `APP_NAME` | Yes | `ZenvyDesk API` | Application name |
| `APP_ENV` | Yes | `production` | Environment mode |
| `APP_BASE_URL` | Yes | `https://api.zenvydesk.site` | Public API URL |
| `FRONTEND_BASE_URL` | Yes | `https://zenvydesk.site` | Main website URL |
| `FACEBOOK_APP_ID` | Yes | `123456789` | From Facebook Developer Console |
| `FACEBOOK_APP_SECRET` | Yes | `abc123...` | From Facebook Developer Console |
| `FACEBOOK_REDIRECT_URI` | Yes | `https://api.zenvydesk.site/auth/facebook/callback` | OAuth callback URL |
| `FACEBOOK_SCOPES` | Yes | `public_profile,email` | OAuth permissions |
| `DATABASE_URL` | Yes | `sqlite:///./zenvydesk.db` | Database connection |
| `SESSION_EXPIRY_MINUTES` | Yes | `15` | Session timeout |
| `SECRET_KEY` | Yes | Auto-generate | Encryption key |

---

## Production Checklist

Before going live:

- [ ] Service deployed successfully on Render
- [ ] Default Render URL works (`https://zenvydesk-api.onrender.com/health`)
- [ ] Custom domain added in Render
- [ ] DNS CNAME record configured
- [ ] DNS propagated (verified with nslookup)
- [ ] SSL certificate issued (green checkmark in Render)
- [ ] Custom domain works (`https://api.zenvydesk.site/health`)
- [ ] All environment variables set correctly
- [ ] Facebook App configured with production URLs
- [ ] Facebook OAuth redirect tested
- [ ] API documentation accessible (`/docs`)
- [ ] Logs show no errors

---

## Support and Resources

- **Render Documentation:** https://render.com/docs
- **Render Status:** https://status.render.com
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **Facebook OAuth Docs:** https://developers.facebook.com/docs/facebook-login

---

**ZenvyDesk API** - Ready for Render deployment with custom domain support.
