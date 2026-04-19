# Custom Domain Setup for api.zenvydesk.site

## Overview

This document provides detailed instructions for connecting the custom domain `api.zenvydesk.site` to your Render deployment.

**Main Website:** https://zenvydesk.site (remains unchanged)  
**API Backend:** https://api.zenvydesk.site (new subdomain)

## Architecture

```
zenvydesk.site          → Main website (existing)
api.zenvydesk.site      → Backend API (Render)
```

The subdomain `api` will point to your Render service while the main domain continues to serve your website.

## Step-by-Step Setup

### Step 1: Deploy to Render First

Before configuring the custom domain, ensure your service is deployed and working on Render's default URL.

**Test default URL:**
```bash
curl https://zenvydesk-api.onrender.com/health
```

If this returns `{"status":"ok","app":"ZenvyDesk API"}`, proceed to custom domain setup.

### Step 2: Add Custom Domain in Render

1. Log in to https://dashboard.render.com
2. Select your `zenvydesk-api` service
3. Click the **"Settings"** tab
4. Scroll down to **"Custom Domain"** section
5. Click **"Add Custom Domain"**
6. Enter: `api.zenvydesk.site`
7. Click **"Save"**

**Render will display a CNAME target** like:
```
zenvydesk-api.onrender.com
```

**IMPORTANT:** Copy this exact value. You'll need it for DNS configuration.

### Step 3: Configure DNS

Go to your DNS provider where `zenvydesk.site` is managed.

**Common DNS Providers:**
- Cloudflare
- Namecheap
- GoDaddy
- Google Domains
- AWS Route 53

#### For Cloudflare:

1. Log in to Cloudflare
2. Select your domain: `zenvydesk.site`
3. Go to **DNS** → **Records**
4. Click **"Add record"**
5. Configure:
   - **Type:** CNAME
   - **Name:** `api`
   - **Target:** `zenvydesk-api.onrender.com` (use the exact value from Render)
   - **Proxy status:** DNS only (gray cloud icon)
   - **TTL:** Auto
6. Click **"Save"**

**CRITICAL:** Set proxy status to "DNS only" (gray cloud). If proxied (orange cloud), SSL certificate provisioning may fail.

#### For Namecheap:

1. Log in to Namecheap
2. Go to Domain List → Manage
3. Click **"Advanced DNS"**
4. Click **"Add New Record"**
5. Configure:
   - **Type:** CNAME Record
   - **Host:** `api`
   - **Value:** `zenvydesk-api.onrender.com`
   - **TTL:** Automatic
6. Click **"Save"**

#### For GoDaddy:

1. Log in to GoDaddy
2. Go to My Products → DNS
3. Click **"Add"** under Records
4. Configure:
   - **Type:** CNAME
   - **Name:** `api`
   - **Value:** `zenvydesk-api.onrender.com`
   - **TTL:** 1 Hour
5. Click **"Save"**

#### For Google Domains:

1. Log in to Google Domains
2. Select your domain
3. Go to **DNS** → **Custom records**
4. Click **"Create new record"**
5. Configure:
   - **Host name:** `api`
   - **Type:** CNAME
   - **TTL:** 1H
   - **Data:** `zenvydesk-api.onrender.com`
6. Click **"Add"**

### Step 4: Verify DNS Configuration

**Wait 5-10 minutes** for DNS changes to propagate, then verify:

```bash
nslookup api.zenvydesk.site
```

**Expected output:**
```
Server:  8.8.8.8
Address: 8.8.8.8#53

Non-authoritative answer:
Name:    zenvydesk-api.onrender.com
Address: 216.24.57.1
Aliases: api.zenvydesk.site
```

**Alternative verification:**
```bash
dig api.zenvydesk.site
```

**Expected output should include:**
```
api.zenvydesk.site.    300    IN    CNAME    zenvydesk-api.onrender.com.
```

### Step 5: Wait for SSL Certificate

Once DNS is verified, Render automatically provisions an SSL certificate using Let's Encrypt.

**Timeline:**
- DNS propagation: 5-60 minutes
- SSL provisioning: 1-5 minutes after DNS is verified

**Check SSL status in Render:**
1. Go to Render dashboard
2. Select your service
3. Click **"Settings"** → **"Custom Domain"**
4. Look for `api.zenvydesk.site`
5. Status should show: **"Verified"** with a green checkmark

**If status shows "Pending":**
- Wait a few more minutes
- Verify DNS is correctly configured
- Check that CNAME target matches exactly

### Step 6: Test Custom Domain

Once SSL certificate is issued:

**Test with curl:**
```bash
curl https://api.zenvydesk.site/health
```

**Expected response:**
```json
{"status":"ok","app":"ZenvyDesk API"}
```

**Test in browser:**
```
https://api.zenvydesk.site/
```

**Expected response:**
```json
{
  "app": "ZenvyDesk API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

**Test API documentation:**
```
https://api.zenvydesk.site/docs
```

You should see the interactive Swagger UI.

## Common Issues and Solutions

### Issue 1: DNS Not Propagating

**Symptoms:**
- `nslookup api.zenvydesk.site` returns "can't find"
- DNS lookup fails

**Solutions:**
1. Wait longer (DNS can take up to 1 hour)
2. Verify CNAME record is saved correctly
3. Check for typos in the record
4. Ensure you're adding to the correct domain
5. Try flushing local DNS cache:
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Mac/Linux
   sudo dscacheutil -flushcache
   ```

### Issue 2: SSL Certificate Not Provisioning

**Symptoms:**
- Custom domain shows "Pending" in Render
- HTTPS doesn't work
- Browser shows SSL error

**Solutions:**
1. Verify DNS is fully propagated (use nslookup)
2. Check CNAME target matches exactly
3. If using Cloudflare, ensure proxy is disabled (gray cloud)
4. Wait longer (can take up to 30 minutes)
5. Try removing and re-adding the custom domain in Render

### Issue 3: Wrong CNAME Target

**Symptoms:**
- DNS resolves but site doesn't load
- 404 or connection errors

**Solutions:**
1. Go back to Render dashboard
2. Check the exact CNAME target provided
3. Update DNS record with correct target
4. Wait for DNS to propagate again

### Issue 4: Cloudflare Proxy Issues

**Symptoms:**
- SSL certificate won't provision
- Mixed content warnings

**Solutions:**
1. In Cloudflare DNS settings
2. Click the orange cloud next to `api` record
3. Change to gray cloud (DNS only)
4. Wait for changes to propagate
5. Check Render dashboard for SSL status

### Issue 5: Multiple CNAME Records

**Symptoms:**
- Inconsistent behavior
- DNS resolution errors

**Solutions:**
1. Check DNS settings for duplicate records
2. Remove any old or incorrect CNAME records for `api`
3. Keep only one CNAME record pointing to Render
4. Save and wait for propagation

## DNS Propagation Checker

Use online tools to check DNS propagation globally:

- https://www.whatsmydns.net/#CNAME/api.zenvydesk.site
- https://dnschecker.org/#CNAME/api.zenvydesk.site

These tools show DNS status from multiple locations worldwide.

## SSL Certificate Details

Render uses Let's Encrypt for SSL certificates:

- **Issuer:** Let's Encrypt
- **Validity:** 90 days
- **Auto-renewal:** Yes (Render handles this automatically)
- **Type:** Domain Validated (DV)

**To view certificate details:**
```bash
openssl s_client -connect api.zenvydesk.site:443 -servername api.zenvydesk.site < /dev/null
```

## Updating DNS Later

If you need to change the CNAME target later:

1. Get new target from Render
2. Update CNAME record in DNS
3. Wait for propagation (5-60 minutes)
4. Render will automatically update SSL certificate

## Removing Custom Domain

If you need to remove the custom domain:

1. In Render dashboard, go to Settings → Custom Domain
2. Click the trash icon next to `api.zenvydesk.site`
3. Confirm removal
4. Optionally, remove the CNAME record from DNS

## Best Practices

✅ **Do:**
- Use CNAME records (not A records)
- Copy the exact CNAME target from Render
- Wait for DNS propagation before testing
- Keep DNS TTL at default or 1 hour
- Monitor Render dashboard for SSL status

❌ **Don't:**
- Use A records for subdomains pointing to Render
- Add trailing dots unless required by DNS provider
- Enable Cloudflare proxy (orange cloud)
- Change CNAME target manually
- Delete the record while troubleshooting

## Verification Checklist

Before considering setup complete:

- [ ] CNAME record added in DNS
- [ ] DNS resolves correctly (nslookup test passes)
- [ ] Render shows "Verified" status
- [ ] HTTPS works (no SSL errors)
- [ ] `/health` endpoint returns 200 OK
- [ ] API documentation accessible at `/docs`
- [ ] Facebook OAuth redirect works

## Support

If you encounter issues:

1. Check Render status page: https://status.render.com
2. Review Render documentation: https://render.com/docs/custom-domains
3. Check DNS provider documentation
4. Contact Render support if SSL won't provision after 1 hour

---

**ZenvyDesk API** - Custom domain setup for production deployment.
