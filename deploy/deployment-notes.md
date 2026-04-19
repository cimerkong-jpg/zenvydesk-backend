# ZenvyDesk API - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the ZenvyDesk API backend to a production Linux server (Ubuntu/Debian). The backend will be accessible at `https://api.zenvydesk.site`.

**Product Description:**
ZenvyDesk is an AI-powered desktop tool for content creation and workflow assistance. This backend provides secure Facebook OAuth authentication for user login. All actions are user-initiated and user-controlled.

## Architecture

```
Internet
    ↓
DNS: api.zenvydesk.site → Server IP
    ↓
Nginx (Port 443 HTTPS)
    ↓
Reverse Proxy
    ↓
Gunicorn + Uvicorn Workers (Port 8000, localhost only)
    ↓
FastAPI Application
    ↓
SQLite/PostgreSQL Database
```

## Prerequisites

### Server Requirements

- **Operating System**: Ubuntu 20.04+ or Debian 10+
- **RAM**: Minimum 1GB (2GB+ recommended)
- **Python**: 3.9 or higher
- **Root or sudo access**: Required for installation
- **Open Ports**: 80 (HTTP), 443 (HTTPS)

### DNS Requirements

Before deployment, ensure:

1. **Subdomain created**: `api.zenvydesk.site`
2. **DNS A record**: Points to your server's IP address
3. **DNS propagation**: Wait 5-60 minutes after creating the record
4. **Verification**: Run `nslookup api.zenvydesk.site` to confirm

### Facebook App Configuration

Configure your Facebook App at https://developers.facebook.com/apps/:

1. **App Domains**: `zenvydesk.site`
2. **Valid OAuth Redirect URIs**: 
   - `https://api.zenvydesk.site/auth/facebook/callback`
3. **Privacy Policy URL**: `https://zenvydesk.site/privacy-policy`
4. **Terms of Service URL**: `https://zenvydesk.site/terms-of-service`
5. **Data Deletion URL**: `https://zenvydesk.site/data-deletion`
6. **Permissions**: `public_profile`, `email`

## Deployment Steps

### Step 1: Prepare Server

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Install Gunicorn system-wide (optional, we'll use venv version)
# sudo apt install -y gunicorn
```

### Step 2: Create Deployment Directory

```bash
# Create application directory
sudo mkdir -p /opt/zenvydesk-api
sudo chown $USER:$USER /opt/zenvydesk-api

# Create log directories
sudo mkdir -p /var/log/zenvydesk
sudo chown www-data:www-data /var/log/zenvydesk

# Create run directory for PID file
sudo mkdir -p /var/run/zenvydesk
sudo chown www-data:www-data /var/run/zenvydesk
```

### Step 3: Upload Application Code

**Option A: Using Git (Recommended)**

```bash
cd /opt/zenvydesk-api
git clone <your-repo-url> .
# Or if already cloned locally, use rsync/scp to upload
```

**Option B: Using SCP from local machine**

```bash
# From your local machine (Windows)
scp -r C:\Users\Admin\Desktop\BackenPython/* user@your-server-ip:/opt/zenvydesk-api/
```

**Option C: Manual upload via FTP/SFTP**

Use FileZilla or WinSCP to upload all files to `/opt/zenvydesk-api/`

### Step 4: Create Python Virtual Environment

```bash
cd /opt/zenvydesk-api

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install gunicorn if not in requirements.txt
pip install gunicorn
```

### Step 5: Configure Environment Variables

```bash
# Copy production environment template
cp deploy/env.production.example .env

# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env file with your actual values
nano .env
```

**Required values to update in `.env`:**

- `FACEBOOK_APP_ID`: Your Facebook App ID
- `FACEBOOK_APP_SECRET`: Your Facebook App Secret
- `SECRET_KEY`: The generated secure random string
- `DATABASE_URL`: Update if using PostgreSQL

### Step 6: Test Application Locally

```bash
# Still in /opt/zenvydesk-api with venv activated
cd /opt/zenvydesk-api
source venv/bin/activate

# Test with uvicorn directly
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# In another terminal, test the health endpoint
curl http://127.0.0.1:8000/health

# Expected output:
# {"status":"ok","app":"ZenvyDesk API"}

# If successful, stop uvicorn (Ctrl+C)
```

### Step 7: Configure Nginx

```bash
# Copy nginx configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/api.zenvydesk.site

# Create symlink to enable site
sudo ln -s /etc/nginx/sites-available/api.zenvydesk.site /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

### Step 8: Obtain SSL Certificate

```bash
# Install certbot if not already installed
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate for api.zenvydesk.site
sudo certbot --nginx -d api.zenvydesk.site

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)

# Verify certificate
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

**Note**: If certbot fails, ensure:
1. DNS is properly configured and propagated
2. Port 80 is open and accessible
3. Nginx is running: `sudo systemctl status nginx`

### Step 9: Install Systemd Service

```bash
# Copy service file
sudo cp deploy/zenvydesk-api.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable zenvydesk-api

# Start the service
sudo systemctl start zenvydesk-api

# Check service status
sudo systemctl status zenvydesk-api
```

**Expected output:**
```
● zenvydesk-api.service - ZenvyDesk API - AI-powered desktop tool backend
   Loaded: loaded (/etc/systemd/system/zenvydesk-api.service; enabled)
   Active: active (running) since ...
```

### Step 10: Verify Deployment

```bash
# Check if service is running
sudo systemctl status zenvydesk-api

# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000

# Check application logs
sudo journalctl -u zenvydesk-api -f

# Check nginx logs
sudo tail -f /var/log/nginx/api.zenvydesk.site.access.log
sudo tail -f /var/log/nginx/api.zenvydesk.site.error.log

# Check application logs
sudo tail -f /var/log/zenvydesk/access.log
sudo tail -f /var/log/zenvydesk/error.log
```

## Testing the Deployment

### Test 1: Health Check (Local)

```bash
curl http://127.0.0.1:8000/health
```

**Expected:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

### Test 2: Health Check (HTTPS)

```bash
curl https://api.zenvydesk.site/health
```

**Expected:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

### Test 3: Root Endpoint

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

### Test 4: API Documentation

Open in browser:
```
https://api.zenvydesk.site/docs
```

You should see the interactive FastAPI documentation.

### Test 5: Facebook OAuth Login

Open in browser:
```
https://api.zenvydesk.site/auth/facebook/login
```

**Expected behavior:**
- Redirects to Facebook OAuth page
- Shows Facebook login dialog
- After login, redirects back to callback URL

**If it fails**, check:
1. Facebook App ID and Secret are correct in `.env`
2. Redirect URI matches exactly in Facebook App settings
3. Application is reading environment variables correctly

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status zenvydesk-api

# View detailed logs
sudo journalctl -u zenvydesk-api -n 50 --no-pager

# Common issues:
# 1. Missing dependencies: Reinstall with pip
# 2. Permission errors: Check file ownership
# 3. Port already in use: Check with netstat
# 4. Environment file missing: Verify .env exists
```

### Nginx Errors

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx error log
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# If renewal fails, check:
# 1. DNS is correct
# 2. Port 80 is accessible
# 3. Nginx is running
```

### Database Errors

```bash
# Check if database file exists
ls -la /opt/zenvydesk-api/zenvydesk.db

# Check permissions
sudo chown www-data:www-data /opt/zenvydesk-api/zenvydesk.db

# Recreate database (WARNING: deletes all data)
rm /opt/zenvydesk-api/zenvydesk.db
sudo systemctl restart zenvydesk-api
```

### Facebook OAuth Errors

**Error: "Invalid OAuth redirect URI"**
- Verify redirect URI in Facebook App matches exactly: `https://api.zenvydesk.site/auth/facebook/callback`
- Check for trailing slashes or typos

**Error: "App not set up"**
- Ensure Facebook App is in Live mode (not Development)
- Add test users if still in Development mode

**Error: "Invalid app ID"**
- Verify `FACEBOOK_APP_ID` in `.env` is correct
- Restart service after changing `.env`: `sudo systemctl restart zenvydesk-api`

## Maintenance

### Updating the Application

```bash
# Stop the service
sudo systemctl stop zenvydesk-api

# Backup database
cp /opt/zenvydesk-api/zenvydesk.db /opt/zenvydesk-api/zenvydesk.db.backup

# Pull latest code (if using git)
cd /opt/zenvydesk-api
git pull

# Or upload new files via SCP/FTP

# Activate venv and update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start zenvydesk-api

# Check status
sudo systemctl status zenvydesk-api
```

### Viewing Logs

```bash
# Service logs (systemd)
sudo journalctl -u zenvydesk-api -f

# Application logs (gunicorn)
sudo tail -f /var/log/zenvydesk/access.log
sudo tail -f /var/log/zenvydesk/error.log

# Nginx logs
sudo tail -f /var/log/nginx/api.zenvydesk.site.access.log
sudo tail -f /var/log/nginx/api.zenvydesk.site.error.log
```

### Restarting Services

```bash
# Restart application
sudo systemctl restart zenvydesk-api

# Reload application (graceful restart)
sudo systemctl reload zenvydesk-api

# Restart nginx
sudo systemctl restart nginx

# Reload nginx (graceful restart)
sudo systemctl reload nginx
```

## Security Checklist

- [ ] Strong `SECRET_KEY` generated and set
- [ ] `.env` file has restricted permissions (600)
- [ ] Database file has restricted permissions
- [ ] Firewall configured (UFW or iptables)
- [ ] SSH key authentication enabled
- [ ] Root login disabled
- [ ] Regular security updates scheduled
- [ ] SSL certificate auto-renewal working
- [ ] Application logs monitored
- [ ] Backup strategy implemented

## Alternative Deployment Options

If your current hosting environment doesn't support the above setup, consider:

### Option 1: Platform-as-a-Service (PaaS)

**Render.com:**
- Easy Python deployment
- Automatic HTTPS
- Free tier available
- Deploy from GitHub

**Railway.app:**
- Simple deployment
- Automatic HTTPS
- GitHub integration

**Fly.io:**
- Global edge deployment
- Dockerfile support
- Free tier available

### Option 2: Containerized Deployment

If Docker is available, create a `Dockerfile` and deploy with Docker Compose.

### Option 3: Shared Hosting with Python Support

Some shared hosting providers support Python apps via:
- Passenger
- CGI/WSGI
- Custom Python installations

Check with your hosting provider for specific instructions.

## Support

For deployment issues:
1. Check logs first (systemd, nginx, application)
2. Verify all prerequisites are met
3. Ensure DNS and SSL are properly configured
4. Test each component individually
5. Review Facebook App configuration

## Production Checklist

Before going live:

- [ ] DNS configured for api.zenvydesk.site
- [ ] SSL certificate obtained and working
- [ ] Facebook App configured with production URLs
- [ ] Environment variables set correctly
- [ ] Database backed up
- [ ] Service starts automatically on boot
- [ ] Health endpoint returns 200 OK
- [ ] OAuth flow tested end-to-end
- [ ] Logs are being written correctly
- [ ] Monitoring set up (optional but recommended)

---

**ZenvyDesk API** - An AI-powered desktop tool backend for secure user authentication and workflow assistance.
