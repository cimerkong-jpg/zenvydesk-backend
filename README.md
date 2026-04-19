# ZenvyDesk API

Production-ready Python backend for ZenvyDesk - An AI-powered desktop tool for content creation and workflow assistance. This backend handles Facebook OAuth authentication for secure user login.

## Overview

ZenvyDesk API is a FastAPI-based backend that provides:

- Facebook OAuth 2.0 authentication
- Session-based login flow for desktop applications
- Secure user account management
- Meta-compliant data deletion endpoint
- Clean, production-ready architecture

## Architecture

### Public OAuth Flow

This backend implements a public OAuth flow designed for desktop applications:

1. **Desktop app** generates or obtains a `session_id`
2. **Desktop app** opens user's browser to:
   ```
   https://api.zenvydesk.site/auth/facebook/login?session_id=<session_id>
   ```
3. **Backend** creates a login session and redirects to Facebook OAuth
4. **User** authenticates with Facebook in their browser
5. **Facebook** redirects back to:
   ```
   https://api.zenvydesk.site/auth/facebook/callback
   ```
6. **Backend** validates OAuth response, creates/updates user, and displays success page
7. **Desktop app** polls:
   ```
   GET https://api.zenvydesk.site/auth/session/<session_id>
   ```
8. **Desktop app** receives login status and user information

This architecture eliminates the need for localhost callbacks or custom URI schemes.

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── db/
│   │   ├── base.py            # Database engine and base
│   │   └── session.py         # Database session dependency
│   ├── models/
│   │   ├── user.py            # User model
│   │   ├── oauth_identity.py  # OAuth identity model
│   │   └── login_session.py   # Login session model
│   ├── schemas/
│   │   └── auth.py            # Pydantic schemas
│   ├── services/
│   │   ├── facebook_oauth_service.py  # Facebook OAuth logic
│   │   ├── user_service.py            # User management
│   │   └── session_service.py         # Session management
│   ├── routes/
│   │   ├── health.py          # Health check endpoint
│   │   ├── auth_facebook.py   # Facebook OAuth routes
│   │   ├── auth_session.py    # Session polling endpoint
│   │   └── data_deletion.py   # Data deletion endpoint
│   ├── templates/
│   │   ├── auth_success.html  # OAuth success page
│   │   └── auth_error.html    # OAuth error page
│   └── utils/
│       ├── security.py        # Security utilities
│       └── logging.py         # Logging utilities
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints

### Health Check
- `GET /health` - Returns API status

### Authentication
- `GET /auth/facebook/login?session_id=<id>` - Initiate Facebook OAuth
- `GET /auth/facebook/callback` - Facebook OAuth callback (browser only)
- `GET /auth/session/{session_id}` - Poll login session status (desktop app)
- `POST /auth/facebook/data-deletion` - Handle data deletion requests

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Facebook App with OAuth configured

### Local Development Setup

1. **Clone or navigate to the project directory**
   ```bash
   cd BackenPython
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```
   
   Edit `.env` and fill in your values:
   ```env
   FACEBOOK_APP_ID=your_facebook_app_id
   FACEBOOK_APP_SECRET=your_facebook_app_secret
   SECRET_KEY=generate_a_random_secret_key_here
   ```
   
   Generate a secure SECRET_KEY:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   
   Or:
   ```bash
   python app/main.py
   ```

6. **Test the API**
   
   Open your browser to:
   - http://localhost:8000 - Root endpoint
   - http://localhost:8000/docs - Interactive API documentation
   - http://localhost:8000/health - Health check

## Facebook App Configuration

To use this backend with Facebook OAuth, configure your Facebook App with these settings:

### App Domains
```
zenvydesk.site
```

### Valid OAuth Redirect URIs
```
https://api.zenvydesk.site/auth/facebook/callback
http://localhost:8000/auth/facebook/callback  (for development)
```

### Required URLs

Configure these in your Facebook App settings:

- **Privacy Policy URL**: `https://zenvydesk.site/privacy-policy`
- **Terms of Service URL**: `https://zenvydesk.site/terms-of-service`
- **Data Deletion Instructions URL**: `https://zenvydesk.site/data-deletion`

### Permissions

Request only minimal permissions:
- `public_profile` (default)
- `email`

## Production Deployment

### Environment Configuration

For production deployment, update your `.env` file:

```env
APP_ENV=production
APP_BASE_URL=https://api.zenvydesk.site
FRONTEND_BASE_URL=https://zenvydesk.site
FACEBOOK_REDIRECT_URI=https://api.zenvydesk.site/auth/facebook/callback
DATABASE_URL=sqlite:///./zenvydesk.db  # or PostgreSQL/MySQL connection string
```

### Database

For production, consider using PostgreSQL or MySQL instead of SQLite:

```env
# PostgreSQL example
DATABASE_URL=postgresql://user:password@localhost/zenvydesk

# MySQL example
DATABASE_URL=mysql+pymysql://user:password@localhost/zenvydesk
```

Install the appropriate database driver:
```bash
pip install psycopg2-binary  # PostgreSQL
# or
pip install pymysql          # MySQL
```

### Running in Production

Use a production ASGI server like Gunicorn with Uvicorn workers:

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Deployment Checklist

- [ ] Set `APP_ENV=production` in environment
- [ ] Use strong `SECRET_KEY` (never commit to git)
- [ ] Configure production database (PostgreSQL/MySQL recommended)
- [ ] Set up HTTPS/SSL certificate
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Configure Facebook App for production domain
- [ ] Test OAuth flow end-to-end
- [ ] Implement backup strategy for database
- [ ] Review and test data deletion endpoint

## Desktop App Integration

### Login Flow Implementation

Your desktop application should implement this flow:

```python
import requests
import webbrowser
import time
import secrets

# 1. Generate session ID
session_id = secrets.token_urlsafe(32)

# 2. Open browser to login URL
login_url = f"https://api.zenvydesk.site/auth/facebook/login?session_id={session_id}"
webbrowser.open(login_url)

# 3. Poll for login status
while True:
    response = requests.get(f"https://api.zenvydesk.site/auth/session/{session_id}")
    data = response.json()
    
    if data["status"] == "success":
        print(f"Login successful! User: {data['user_name']}")
        user_id = data["user_id"]
        break
    elif data["status"] == "failed":
        print(f"Login failed: {data['error_message']}")
        break
    elif data["status"] == "expired":
        print("Login session expired")
        break
    
    # Still pending, wait and retry
    time.sleep(2)
```

## Security Considerations

- All secrets are stored in environment variables
- OAuth state parameter prevents CSRF attacks
- Session IDs are cryptographically secure random tokens
- Access tokens are stored securely (consider encryption for production)
- Input validation on all endpoints
- Sensitive data is redacted from logs
- HTTPS required for production

## Meta Review Guidelines

This backend is designed with Meta app review in mind:

### Product Positioning

ZenvyDesk is an AI-powered desktop tool for:
- Content creation and workflow assistance
- User-controlled actions and scheduling
- Secure authentication via Facebook Login

### Key Points for Review

- All user actions are user-initiated and controlled
- Minimal OAuth permissions requested (public_profile, email)
- Data deletion endpoint implemented
- Privacy policy and terms of service required
- No automated posting or spam functionality
- Professional, trust-building user experience

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

### Code Quality

```bash
# Format code
pip install black
black app/

# Lint code
pip install flake8
flake8 app/
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Make sure you're running from the project root and virtual environment is activated

**Issue**: Database errors on startup
- **Solution**: Delete `zenvydesk.db` and restart to recreate tables

**Issue**: Facebook OAuth errors
- **Solution**: Verify your Facebook App ID, Secret, and Redirect URI are correct

**Issue**: CORS errors from desktop app
- **Solution**: Add your desktop app's origin to CORS configuration in `main.py`

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review Facebook OAuth documentation
- Ensure all environment variables are set correctly

## License

Proprietary - ZenvyDesk

---

**Built with FastAPI, SQLAlchemy, and modern Python best practices.**
