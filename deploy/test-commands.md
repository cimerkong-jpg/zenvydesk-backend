# ZenvyDesk API - Test Commands

This document provides exact commands to test your ZenvyDesk API deployment at each stage.

## Pre-Deployment Tests

### Test 1: Verify DNS Configuration

```bash
# Check if DNS is configured correctly
nslookup api.zenvydesk.site

# Expected output should show your server's IP address
# Example:
# Server:  8.8.8.8
# Address: 8.8.8.8#53
#
# Non-authoritative answer:
# Name:    api.zenvydesk.site
# Address: YOUR_SERVER_IP
```

### Test 2: Verify Python Installation

```bash
# Check Python version (must be 3.9+)
python3 --version

# Expected: Python 3.9.x or higher
```

### Test 3: Verify Required Packages

```bash
# Check if nginx is installed
nginx -v

# Check if certbot is installed
certbot --version
```

## Local Application Tests

### Test 4: Test Application Locally (Before Systemd)

```bash
# Navigate to application directory
cd /opt/zenvydesk-api

# Activate virtual environment
source venv/bin/activate

# Start application manually
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Test 5: Test Health Endpoint (Local)

**In a new terminal:**

```bash
curl http://127.0.0.1:8000/health
```

**Expected output:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**HTTP Status:** 200 OK

### Test 6: Test Root Endpoint (Local)

```bash
curl http://127.0.0.1:8000/
```

**Expected output:**
```json
{
  "app":"ZenvyDesk API",
  "version":"1.0.0",
  "status":"running",
  "docs":"/docs"
}
```

**HTTP Status:** 200 OK

### Test 7: Test Session Endpoint (Local)

```bash
curl http://127.0.0.1:8000/auth/session/test-session-id
```

**Expected output:**
```json
{
  "status":"pending",
  "user_id":null,
  "user_name":null,
  "user_email":null,
  "error_message":null
}
```

**Note:** This will return 404 if session doesn't exist, which is expected for a test ID.

## Systemd Service Tests

### Test 8: Check Service Status

```bash
sudo systemctl status zenvydesk-api
```

**Expected output:**
```
● zenvydesk-api.service - ZenvyDesk API - AI-powered desktop tool backend
   Loaded: loaded (/etc/systemd/system/zenvydesk-api.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2024-01-01 12:00:00 UTC; 5min ago
 Main PID: 12345 (gunicorn)
    Tasks: 5 (limit: 4915)
   Memory: 150.0M
   CGroup: /system.slice/zenvydesk-api.service
           ├─12345 /opt/zenvydesk-api/venv/bin/python3 /opt/zenvydesk-api/venv/bin/gunicorn...
           └─12346 /opt/zenvydesk-api/venv/bin/python3 /opt/zenvydesk-api/venv/bin/gunicorn...
```

**Key indicators:**
- `Active: active (running)` - Service is running
- No error messages in the output

### Test 9: Check if Port is Listening

```bash
sudo netstat -tlnp | grep 8000
```

**Expected output:**
```
tcp        0      0 127.0.0.1:8000          0.0.0.0:*               LISTEN      12345/python3
```

**Alternative command:**
```bash
sudo ss -tlnp | grep 8000
```

### Test 10: View Service Logs

```bash
# View last 50 lines of service logs
sudo journalctl -u zenvydesk-api -n 50 --no-pager

# Follow logs in real-time
sudo journalctl -u zenvydesk-api -f
```

**Expected:** No error messages, should show startup logs

## Nginx Tests

### Test 11: Test Nginx Configuration

```bash
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Test 12: Check Nginx Status

```bash
sudo systemctl status nginx
```

**Expected:** `Active: active (running)`

### Test 13: Test HTTP to HTTPS Redirect

```bash
curl -I http://api.zenvydesk.site
```

**Expected output:**
```
HTTP/1.1 301 Moved Permanently
Server: nginx
Location: https://api.zenvydesk.site/
```

**HTTP Status:** 301 (redirect)

## SSL Certificate Tests

### Test 14: Verify SSL Certificate

```bash
sudo certbot certificates
```

**Expected output:**
```
Found the following certs:
  Certificate Name: api.zenvydesk.site
    Domains: api.zenvydesk.site
    Expiry Date: 2024-04-01 12:00:00+00:00 (VALID: 89 days)
    Certificate Path: /etc/letsencrypt/live/api.zenvydesk.site/fullchain.pem
    Private Key Path: /etc/letsencrypt/live/api.zenvydesk.site/privkey.pem
```

### Test 15: Test SSL Connection

```bash
curl -I https://api.zenvydesk.site
```

**Expected output:**
```
HTTP/2 200
server: nginx
date: Mon, 01 Jan 2024 12:00:00 GMT
content-type: application/json
```

**HTTP Status:** 200 OK

**Alternative SSL test:**
```bash
openssl s_client -connect api.zenvydesk.site:443 -servername api.zenvydesk.site < /dev/null
```

**Expected:** Should show certificate details without errors

## Production API Tests

### Test 16: Health Check (HTTPS)

```bash
curl https://api.zenvydesk.site/health
```

**Expected output:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**HTTP Status:** 200 OK

### Test 17: Root Endpoint (HTTPS)

```bash
curl https://api.zenvydesk.site/
```

**Expected output:**
```json
{
  "app":"ZenvyDesk API",
  "version":"1.0.0",
  "status":"running",
  "docs":"/docs"
}
```

**HTTP Status:** 200 OK

### Test 18: API Documentation

**Open in browser:**
```
https://api.zenvydesk.site/docs
```

**Expected:**
- Interactive Swagger UI documentation
- List of all available endpoints
- Ability to test endpoints directly

### Test 19: Test with Verbose Output

```bash
curl -v https://api.zenvydesk.site/health
```

**Expected:** Full HTTP headers and response, no SSL errors

## Facebook OAuth Tests

### Test 20: Test Facebook Login Redirect

**Open in browser:**
```
https://api.zenvydesk.site/auth/facebook/login
```

**Expected behavior:**
1. Browser redirects to Facebook
2. URL should be: `https://www.facebook.com/v18.0/dialog/oauth?client_id=...`
3. Facebook login page appears

**If it fails:**
- Check browser console for errors
- Verify Facebook App ID in `.env`
- Check service logs: `sudo journalctl -u zenvydesk-api -n 50`

### Test 21: Test Facebook Login with Session ID

**Open in browser:**
```
https://api.zenvydesk.site/auth/facebook/login?session_id=test-123
```

**Expected:** Same as Test 20, but with session tracking

### Test 22: Test Session Status Endpoint

```bash
# Create a test session first by visiting the login URL
# Then check its status
curl https://api.zenvydesk.site/auth/session/test-123
```

**Expected output (if session doesn't exist):**
```json
{"detail":"Session not found"}
```

**HTTP Status:** 404

**Expected output (if session exists and is pending):**
```json
{
  "status":"pending",
  "user_id":null,
  "user_name":null,
  "user_email":null,
  "error_message":null
}
```

**HTTP Status:** 200 OK

## Performance Tests

### Test 23: Response Time Test

```bash
curl -w "\nTime Total: %{time_total}s\n" -o /dev/null -s https://api.zenvydesk.site/health
```

**Expected:** Response time under 1 second

### Test 24: Concurrent Requests Test

```bash
# Install apache bench if not available
sudo apt install -y apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 https://api.zenvydesk.site/health
```

**Expected:** All requests should succeed (200 OK)

## Log Monitoring Tests

### Test 25: Monitor Application Logs

```bash
# Watch application logs in real-time
sudo tail -f /var/log/zenvydesk/access.log
```

**Expected:** See log entries for each request

### Test 26: Monitor Nginx Access Logs

```bash
sudo tail -f /var/log/nginx/api.zenvydesk.site.access.log
```

**Expected:** See log entries for each HTTPS request

### Test 27: Monitor Nginx Error Logs

```bash
sudo tail -f /var/log/nginx/api.zenvydesk.site.error.log
```

**Expected:** No errors (file may be empty)

### Test 28: Monitor Service Logs

```bash
sudo journalctl -u zenvydesk-api -f
```

**Expected:** See application startup and request logs

## Database Tests

### Test 29: Check Database File

```bash
ls -lh /opt/zenvydesk-api/zenvydesk.db
```

**Expected output:**
```
-rw-r--r-- 1 www-data www-data 20K Jan  1 12:00 /opt/zenvydesk-api/zenvydesk.db
```

### Test 30: Check Database Tables

```bash
cd /opt/zenvydesk-api
source venv/bin/activate
python3 -c "from app.db.base import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

**Expected output:**
```
['users', 'oauth_identities', 'login_sessions']
```

## End-to-End OAuth Flow Test

### Test 31: Complete OAuth Flow

**Step 1:** Open browser to:
```
https://api.zenvydesk.site/auth/facebook/login?session_id=manual-test-001
```

**Step 2:** Complete Facebook login in browser

**Step 3:** After redirect, check session status:
```bash
curl https://api.zenvydesk.site/auth/session/manual-test-001
```

**Expected output (after successful login):**
```json
{
  "status":"success",
  "user_id":1,
  "user_name":"Test User",
  "user_email":"test@example.com",
  "error_message":null
}
```

**HTTP Status:** 200 OK

## Troubleshooting Commands

### Debug: Check Environment Variables

```bash
# View environment file (be careful with secrets)
sudo cat /opt/zenvydesk-api/.env | grep -v SECRET | grep -v PASSWORD
```

### Debug: Test Database Connection

```bash
cd /opt/zenvydesk-api
source venv/bin/activate
python3 -c "from app.db.base import engine; engine.connect(); print('Database connection successful')"
```

### Debug: Check File Permissions

```bash
ls -la /opt/zenvydesk-api/
ls -la /opt/zenvydesk-api/.env
ls -la /opt/zenvydesk-api/zenvydesk.db
```

### Debug: Test Python Import

```bash
cd /opt/zenvydesk-api
source venv/bin/activate
python3 -c "from app.main import app; print('Import successful')"
```

### Debug: Check Firewall

```bash
# Check if UFW is active
sudo ufw status

# Check if ports 80 and 443 are open
sudo ufw status | grep -E '80|443'
```

## Quick Test Script

Save this as `test-deployment.sh`:

```bash
#!/bin/bash

echo "=== ZenvyDesk API Deployment Tests ==="
echo ""

echo "Test 1: DNS Resolution"
nslookup api.zenvydesk.site
echo ""

echo "Test 2: Service Status"
sudo systemctl status zenvydesk-api --no-pager
echo ""

echo "Test 3: Port Listening"
sudo netstat -tlnp | grep 8000
echo ""

echo "Test 4: Nginx Status"
sudo systemctl status nginx --no-pager
echo ""

echo "Test 5: SSL Certificate"
sudo certbot certificates | grep api.zenvydesk.site
echo ""

echo "Test 6: Health Check (HTTPS)"
curl -s https://api.zenvydesk.site/health
echo ""

echo "Test 7: Root Endpoint (HTTPS)"
curl -s https://api.zenvydesk.site/
echo ""

echo "=== All Tests Complete ==="
```

Run with:
```bash
chmod +x test-deployment.sh
./test-deployment.sh
```

## Success Criteria

Your deployment is successful if:

- [ ] DNS resolves to correct IP
- [ ] Service is active and running
- [ ] Port 8000 is listening on localhost
- [ ] Nginx is active and running
- [ ] SSL certificate is valid
- [ ] Health endpoint returns `{"status":"ok","app":"ZenvyDesk API"}`
- [ ] Root endpoint returns version info
- [ ] API docs are accessible at `/docs`
- [ ] Facebook login redirects to Facebook OAuth
- [ ] No errors in service logs
- [ ] No errors in nginx logs

## Common Test Failures and Solutions

### Health Check Returns 502 Bad Gateway

**Cause:** Backend service is not running

**Solution:**
```bash
sudo systemctl start zenvydesk-api
sudo systemctl status zenvydesk-api
```

### Health Check Returns Connection Refused

**Cause:** Nginx is not running or misconfigured

**Solution:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate Error

**Cause:** Certificate not installed or expired

**Solution:**
```bash
sudo certbot --nginx -d api.zenvydesk.site
```

### Facebook OAuth Redirect Error

**Cause:** Wrong redirect URI or app credentials

**Solution:**
1. Check `.env` file for correct Facebook App ID and Secret
2. Verify redirect URI in Facebook App settings
3. Restart service: `sudo systemctl restart zenvydesk-api`

---

**Note:** Always test in order, as later tests depend on earlier ones succeeding.
