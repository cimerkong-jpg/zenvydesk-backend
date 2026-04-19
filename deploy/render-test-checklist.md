# ZenvyDesk API - Render Test Checklist

## Overview

This checklist provides exact testing steps to verify your ZenvyDesk API deployment on Render with the custom domain `api.zenvydesk.site`.

**Test these URLs:**
- https://api.zenvydesk.site/health
- https://api.zenvydesk.site/auth/facebook/login

---

## Pre-Deployment Tests

### Test 1: Local Development Test

Before deploying to Render, test locally:

```bash
# Navigate to project directory
cd c:\Users\Admin\Desktop\BackenPython

# Activate virtual environment (if using one)
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env file first)
# Then run the app
python app/main.py
```

**In another terminal:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**Status:** 200 OK

If this works, proceed to Render deployment.

---

## Render Default URL Tests

After deploying to Render, test the default URL first.

### Test 2: Render Default Health Check

```bash
curl https://zenvydesk-api.onrender.com/health
```

**Expected Response:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**HTTP Status:** 200 OK

**If this fails:**
- Check Render logs for errors
- Verify environment variables are set
- Ensure build completed successfully

### Test 3: Render Default Root Endpoint

```bash
curl https://zenvydesk-api.onrender.com/
```

**Expected Response:**
```json
{
  "app":"ZenvyDesk API",
  "version":"1.0.0",
  "status":"running",
  "docs":"/docs"
}
```

**HTTP Status:** 200 OK

### Test 4: Render Default API Docs

**Open in browser:**
```
https://zenvydesk-api.onrender.com/docs
```

**Expected:**
- Interactive Swagger UI loads
- All endpoints are listed
- Can expand and test endpoints

---

## Custom Domain Tests

After configuring DNS and waiting for SSL certificate.

### Test 5: DNS Resolution

```bash
nslookup api.zenvydesk.site
```

**Expected Output:**
```
Server:  8.8.8.8
Address: 8.8.8.8#53

Non-authoritative answer:
Name:    zenvydesk-api.onrender.com
Address: 216.24.57.1
Aliases: api.zenvydesk.site
```

**If DNS doesn't resolve:**
- Wait longer (up to 1 hour)
- Verify CNAME record is correct
- Check DNS provider settings

### Test 6: Custom Domain Health Check

```bash
curl https://api.zenvydesk.site/health
```

**Expected Response:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**HTTP Status:** 200 OK

**If this fails:**
- Check SSL certificate status in Render
- Verify DNS is fully propagated
- Check Render logs

### Test 7: Custom Domain Root Endpoint

```bash
curl https://api.zenvydesk.site/
```

**Expected Response:**
```json
{
  "app":"ZenvyDesk API",
  "version":"1.0.0",
  "status":"running",
  "docs":"/docs"
}
```

**HTTP Status:** 200 OK

### Test 8: Custom Domain API Docs

**Open in browser:**
```
https://api.zenvydesk.site/docs
```

**Expected:**
- Swagger UI loads without SSL errors
- All endpoints visible
- Can interact with API

### Test 9: Verbose Health Check

```bash
curl -v https://api.zenvydesk.site/health
```

**Expected Output Includes:**
```
* Connected to api.zenvydesk.site
* SSL connection using TLSv1.3
* Server certificate:
*  subject: CN=api.zenvydesk.site
*  issuer: C=US; O=Let's Encrypt
* SSL certificate verify ok
> GET /health HTTP/2
< HTTP/2 200
< content-type: application/json
{"status":"ok","app":"ZenvyDesk API"}
```

**Key indicators:**
- SSL certificate verify ok
- HTTP/2 200
- No SSL errors

---

## Facebook OAuth Tests

### Test 10: Facebook Login Redirect (Browser)

**Open in browser:**
```
https://api.zenvydesk.site/auth/facebook/login
```

**Expected Behavior:**
1. Browser immediately redirects to Facebook
2. URL changes to: `https://www.facebook.com/v18.0/dialog/oauth?client_id=...`
3. Facebook login page appears
4. Shows your app name
5. Requests permissions: public_profile, email

**If redirect doesn't happen:**
- Check browser console for errors
- Verify `FACEBOOK_APP_ID` environment variable is set
- Check Render logs for errors

### Test 11: Facebook Login with Session ID

**Open in browser:**
```
https://api.zenvydesk.site/auth/facebook/login?session_id=test-12345
```

**Expected Behavior:**
- Same as Test 10
- Session ID is tracked in backend
- Can poll session status later

### Test 12: Complete OAuth Flow

**Step 1:** Open browser to:
```
https://api.zenvydesk.site/auth/facebook/login?session_id=manual-test-001
```

**Step 2:** Complete Facebook login

**Step 3:** After redirect, you should see:
- Success page with "Login Successful!"
- Message: "You can now return to the ZenvyDesk application"
- Clean, branded page

**Step 4:** Check session status:
```bash
curl https://api.zenvydesk.site/auth/session/manual-test-001
```

**Expected Response:**
```json
{
  "status":"success",
  "user_id":1,
  "user_name":"Your Name",
  "user_email":"your@email.com",
  "error_message":null
}
```

**HTTP Status:** 200 OK

---

## Session Endpoint Tests

### Test 13: Non-Existent Session

```bash
curl https://api.zenvydesk.site/auth/session/nonexistent-session-id
```

**Expected Response:**
```json
{"detail":"Session not found"}
```

**HTTP Status:** 404

### Test 14: Pending Session

After starting OAuth but before completing:

```bash
curl https://api.zenvydesk.site/auth/session/pending-session-id
```

**Expected Response:**
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

---

## Error Handling Tests

### Test 15: Invalid Endpoint

```bash
curl https://api.zenvydesk.site/invalid-endpoint
```

**Expected Response:**
```json
{"detail":"Not Found"}
```

**HTTP Status:** 404

### Test 16: OAuth Error Handling

**Open in browser:**
```
https://api.zenvydesk.site/auth/facebook/callback?error=access_denied&error_description=User+cancelled
```

**Expected:**
- Error page displays
- Message: "Login could not be completed"
- Clean error handling

---

## Performance Tests

### Test 17: Response Time

```bash
curl -w "\nTime Total: %{time_total}s\n" -o /dev/null -s https://api.zenvydesk.site/health
```

**Expected:**
- Response time under 2 seconds
- Consistent across multiple requests

### Test 18: Multiple Concurrent Requests

```bash
# Run 10 requests
for i in {1..10}; do
  curl -s https://api.zenvydesk.site/health &
done
wait
```

**Expected:**
- All requests succeed
- No errors or timeouts

---

## SSL/Security Tests

### Test 19: SSL Certificate Verification

```bash
openssl s_client -connect api.zenvydesk.site:443 -servername api.zenvydesk.site < /dev/null
```

**Expected Output Includes:**
```
Certificate chain
 0 s:CN = api.zenvydesk.site
   i:C = US, O = Let's Encrypt
Verify return code: 0 (ok)
```

### Test 20: HTTPS Enforcement

```bash
curl -I http://api.zenvydesk.site/health
```

**Expected:**
- Redirect to HTTPS (301 or 302)
- Or direct HTTPS response

---

## Environment Variable Tests

### Test 21: Verify Configuration

Check that environment variables are working:

**Test APP_BASE_URL:**
```bash
curl https://api.zenvydesk.site/ | grep "ZenvyDesk API"
```

**Expected:** Output contains "ZenvyDesk API"

**Test Facebook Configuration:**
- OAuth redirect should use correct domain
- Check Render logs for startup messages

---

## Integration Tests

### Test 22: Desktop App Simulation

Simulate desktop app login flow:

**Step 1: Generate session ID**
```bash
SESSION_ID=$(python -c "import secrets; print(secrets.token_urlsafe(16))")
echo "Session ID: $SESSION_ID"
```

**Step 2: Start OAuth (open in browser)**
```
https://api.zenvydesk.site/auth/facebook/login?session_id=$SESSION_ID
```

**Step 3: Poll for status (in terminal)**
```bash
while true; do
  curl -s https://api.zenvydesk.site/auth/session/$SESSION_ID | jq .status
  sleep 2
done
```

**Expected:**
- Initially shows "pending"
- After completing OAuth in browser, shows "success"
- Desktop app receives user info

---

## Monitoring Tests

### Test 23: Check Render Logs

1. Go to Render dashboard
2. Select zenvydesk-api service
3. Click "Logs" tab
4. Make a request to `/health`
5. Verify log entry appears

**Expected Log Entry:**
```
INFO:     127.0.0.1:12345 - "GET /health HTTP/1.1" 200 OK
```

### Test 24: Error Logging

Trigger an error and check logs:

```bash
curl https://api.zenvydesk.site/auth/session/test-error
```

Check Render logs for error handling.

---

## Final Verification Checklist

Before considering deployment complete:

### Deployment Status
- [ ] Service deployed successfully on Render
- [ ] Build completed without errors
- [ ] Service is running (not crashed)
- [ ] Logs show successful startup

### Default URL Tests
- [ ] Health check works on default URL
- [ ] Root endpoint works on default URL
- [ ] API docs accessible on default URL

### Custom Domain
- [ ] DNS CNAME record configured
- [ ] DNS resolves correctly (nslookup passes)
- [ ] SSL certificate issued (Render shows "Verified")
- [ ] HTTPS works without errors

### API Endpoints
- [ ] `/health` returns 200 OK
- [ ] `/` returns version info
- [ ] `/docs` loads Swagger UI
- [ ] `/auth/facebook/login` redirects to Facebook
- [ ] `/auth/facebook/callback` handles OAuth
- [ ] `/auth/session/{id}` returns session status

### Facebook OAuth
- [ ] Facebook App configured with production URLs
- [ ] OAuth redirect works
- [ ] Login completes successfully
- [ ] Success page displays
- [ ] Session polling works
- [ ] User info returned correctly

### Security
- [ ] HTTPS enforced
- [ ] SSL certificate valid
- [ ] No SSL errors in browser
- [ ] Environment variables secure

### Performance
- [ ] Response time acceptable (< 2s)
- [ ] Multiple requests handled correctly
- [ ] No timeouts or errors

---

## Troubleshooting Quick Reference

### Health Check Fails
```bash
# Check service status in Render dashboard
# View logs for errors
# Verify environment variables
# Test default URL first
```

### OAuth Redirect Fails
```bash
# Verify FACEBOOK_APP_ID is set
# Check FACEBOOK_REDIRECT_URI matches exactly
# Ensure Facebook App has correct redirect URI
# Check Render logs for errors
```

### Custom Domain Not Working
```bash
# Verify DNS with: nslookup api.zenvydesk.site
# Check SSL status in Render dashboard
# Wait for DNS propagation (up to 1 hour)
# Verify CNAME target is correct
```

### Session Polling Returns 404
```bash
# Ensure session was created first
# Check session ID is correct
# Verify route is working: curl /auth/session/test
```

---

## Success Criteria

Your deployment is successful when:

✅ All tests in this checklist pass  
✅ Health endpoint returns 200 OK  
✅ Facebook OAuth completes successfully  
✅ Custom domain works with HTTPS  
✅ No errors in Render logs  
✅ Desktop app can poll session status  

---

**ZenvyDesk API** - Complete test checklist for Render deployment verification.
