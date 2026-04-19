#!/bin/bash

# ZenvyDesk API - Quick Deployment Script
# This script automates the deployment process for Ubuntu/Debian servers
# Run with: sudo bash quick-deploy.sh

set -e  # Exit on error

echo "=========================================="
echo "ZenvyDesk API - Quick Deployment Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Variables
APP_DIR="/opt/zenvydesk-api"
APP_USER="www-data"
APP_GROUP="www-data"
DOMAIN="api.zenvydesk.site"

echo "Step 1: Installing system packages..."
apt update
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

echo ""
echo "Step 2: Creating directories..."
mkdir -p $APP_DIR
mkdir -p /var/log/zenvydesk
mkdir -p /var/run/zenvydesk
chown $APP_USER:$APP_GROUP /var/log/zenvydesk
chown $APP_USER:$APP_GROUP /var/run/zenvydesk

echo ""
echo "Step 3: Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo ""
echo "Step 4: Configuring environment variables..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp deploy/env.production.example .env
    echo "IMPORTANT: Edit $APP_DIR/.env with your actual values!"
    echo "Press Enter to continue after editing .env file..."
    read
fi

echo ""
echo "Step 5: Setting file permissions..."
chown -R $APP_USER:$APP_GROUP $APP_DIR
chmod 600 $APP_DIR/.env

echo ""
echo "Step 6: Testing application locally..."
cd $APP_DIR
source venv/bin/activate
timeout 5 python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
sleep 3
if curl -s http://127.0.0.1:8000/health | grep -q "ok"; then
    echo "✓ Application test successful"
else
    echo "✗ Application test failed"
    exit 1
fi
pkill -f uvicorn

echo ""
echo "Step 7: Installing systemd service..."
cp deploy/zenvydesk-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable zenvydesk-api
systemctl start zenvydesk-api
sleep 2
systemctl status zenvydesk-api --no-pager

echo ""
echo "Step 8: Configuring Nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/$DOMAIN
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

echo ""
echo "Step 9: Obtaining SSL certificate..."
echo "Make sure DNS for $DOMAIN points to this server!"
echo "Press Enter to continue with SSL certificate..."
read
certbot --nginx -d $DOMAIN

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Test your deployment:"
echo "  curl https://$DOMAIN/health"
echo ""
echo "View logs:"
echo "  sudo journalctl -u zenvydesk-api -f"
echo ""
echo "Restart service:"
echo "  sudo systemctl restart zenvydesk-api"
echo ""
echo "Next steps:"
echo "1. Configure Facebook App with production URLs"
echo "2. Test OAuth flow: https://$DOMAIN/auth/facebook/login"
echo "3. Monitor logs for any issues"
echo ""
