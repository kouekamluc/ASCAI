# Google OAuth Setup Guide for ASCAI

This guide will help you set up Google OAuth authentication step-by-step.

## 🔴 Common "Access Denied" Errors

The "access denied" error typically occurs due to:
1. **Incorrect redirect URI** - The callback URL doesn't match what's configured in Google
2. **Missing or wrong Client ID/Secret** - Credentials not set or incorrect
3. **OAuth consent screen not configured** - App not properly set up in Google Cloud
4. **Domain not authorized** - Your domain not added to authorized domains

---

## 📋 Step-by-Step Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter project name: `ASCAI Platform` (or any name you prefer)
5. Click **"Create"**
6. Wait for the project to be created and select it

---

### Step 2: Enable Google+ API (if needed) or OAuth 2.0

1. In your Google Cloud project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google+ API"** (or use **"Identity Toolkit API"**)
3. Click on it and click **"Enable"**
4. Also enable **"People API"** (for profile information)

**Note:** Google+ API is deprecated, but some OAuth flows may still need it. The People API is the modern replacement.

---

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace account, then choose "Internal")
3. Click **"Create"**

#### Fill in the OAuth Consent Screen:

**App Information:**
- **App name:** `ASCAI Platform` (or your preferred name)
- **User support email:** Your email address
- **App logo:** (Optional) Upload your logo
- **Application home page:** `https://your-domain.com` (your production URL)
- **Application privacy policy link:** `https://your-domain.com/privacy/` (if you have one)
- **Application terms of service link:** `https://your-domain.com/terms/` (if you have one)
- **Authorized domains:** Add your domain (e.g., `your-domain.com`, `onrender.com` for Render)
- **Developer contact information:** Your email address

**Scopes:**
- Click **"Add or Remove Scopes"**
- Select:
  - `.../auth/userinfo.email`
  - `.../auth/userinfo.profile`
  - `openid`
- Click **"Update"**

**Test users (if app is in Testing mode):**
- Add test email addresses that can use the app
- **Important:** If your app is in "Testing" mode, only these users can authenticate

**Save and Continue** through all steps until you reach the summary.

---

### Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. If prompted, select **"Web application"** as the application type
4. Fill in the form:

**Name:** `ASCAI Web Client` (or any name)

**Authorized JavaScript origins:**
Add these URLs (one per line):
```
http://localhost:8000
https://your-domain.com
https://www.your-domain.com
https://your-app-name.onrender.com
```

**Authorized redirect URIs:**
Add these URLs (one per line):
```
http://localhost:8000/accounts/google/login/callback/
https://your-domain.com/accounts/google/login/callback/
https://www.your-domain.com/accounts/google/login/callback/
https://your-app-name.onrender.com/accounts/google/login/callback/
```

**Important Notes:**
- The callback URL **MUST** end with `/accounts/google/login/callback/` (trailing slash is important!)
- Add **both** `http://localhost:8000` (for development) and your production URLs
- If using Render, add your Render URL: `https://your-app-name.onrender.com`

5. Click **"Create"**
6. **Copy the Client ID and Client Secret** - You'll need these!

---

### Step 5: Get Your Credentials

After creating the OAuth client, you'll see:
- **Client ID:** Something like `123456789-abc123def456.apps.googleusercontent.com`
- **Client Secret:** Something like `GOCSPX-abc123def456xyz789`

**⚠️ Important:** Save these securely! The Client Secret is only shown once.

---

### Step 6: Update Your Environment Variables

#### For Development (.env file):

```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-abc123def456xyz789
```

#### For Production (Render Environment):

1. Go to your Render dashboard
2. Select your Web Service
3. Go to **Environment** tab
4. Add these variables:

```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-abc123def456xyz789
```

**Replace with your actual values!**

---

### Step 7: Verify Django Site Configuration

Make sure your Django site is configured correctly:

1. Go to Django Admin: `https://your-domain.com/admin/`
2. Navigate to **"Sites"** → **"Sites"**
3. Edit the site (usually ID=1)
4. Set:
   - **Domain name:** `your-domain.com` (or your Render URL)
   - **Display name:** `ASCAI Platform`
5. Save

**Or via Django shell:**
```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'your-domain.com'  # or 'your-app.onrender.com'
site.name = 'ASCAI Platform'
site.save()
```

---

## 🔍 Troubleshooting "Access Denied" Errors

### Error: "redirect_uri_mismatch"

**Problem:** The redirect URI in your request doesn't match what's configured in Google.

**Solution:**
1. Check the exact callback URL in your error message
2. Go to Google Cloud Console → Credentials → Your OAuth Client
3. Make sure the redirect URI in the error matches exactly what's in "Authorized redirect URIs"
4. **Important:** The URL must include the trailing slash: `/accounts/google/login/callback/`
5. Make sure you're using `https://` in production (not `http://`)

### Error: "access_denied" (User clicked Cancel)

**Problem:** User clicked "Cancel" on the Google consent screen.

**Solution:** This is normal user behavior. Make sure your consent screen is properly configured.

### Error: "invalid_client"

**Problem:** Client ID or Secret is incorrect.

**Solution:**
1. Double-check your `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`
2. Make sure there are no extra spaces or quotes
3. Regenerate credentials if needed

### Error: "unauthorized_client"

**Problem:** The OAuth client is not authorized for this application type.

**Solution:**
1. Make sure you created a **"Web application"** OAuth client (not Desktop or iOS)
2. Check that your domain is in "Authorized domains" in OAuth consent screen

### Error: App is in "Testing" mode

**Problem:** Your app is in testing mode and the user's email is not in test users list.

**Solution:**
1. Go to OAuth consent screen
2. Add the user's email to "Test users"
3. Or publish your app (requires verification if requesting sensitive scopes)

---

## ✅ Testing the Setup

### 1. Test Locally (Development)

1. Make sure your `.env` file has:
   ```bash
   GOOGLE_OAUTH_CLIENT_ID=your-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   ```

2. Start your development server:
   ```bash
   python manage.py runserver
   ```

3. Go to: `http://localhost:8000/accounts/login/`
4. Click "Continue with Google"
5. You should be redirected to Google's login page
6. After logging in, you should be redirected back to your app

### 2. Test in Production

1. Make sure environment variables are set in Render
2. Make sure your production URL is in "Authorized redirect URIs"
3. Visit: `https://your-domain.com/accounts/login/`
4. Click "Continue with Google"
5. Test the full flow

---

## 📝 Quick Checklist

Before testing, make sure:

- [ ] Google Cloud project created
- [ ] OAuth consent screen configured
- [ ] OAuth 2.0 credentials created (Web application type)
- [ ] Authorized redirect URIs include:
  - [ ] `http://localhost:8000/accounts/google/login/callback/` (development)
  - [ ] `https://your-domain.com/accounts/google/login/callback/` (production)
  - [ ] `https://your-app.onrender.com/accounts/google/login/callback/` (if using Render)
- [ ] Client ID and Secret added to environment variables
- [ ] Django Site configured with correct domain
- [ ] App restarted after adding environment variables

---

## 🔐 Security Best Practices

1. **Never commit credentials to git** - Always use environment variables
2. **Use different OAuth clients** for development and production (recommended)
3. **Rotate secrets** if they're ever exposed
4. **Monitor OAuth usage** in Google Cloud Console
5. **Set up alerts** for unusual activity

---

## 📞 What I Need From You

To help you set this up, please provide:

1. **Your production domain/URL** (e.g., `ascai.onrender.com` or `ascai.it`)
2. **Whether you've created the Google Cloud project** (Yes/No)
3. **The exact error message** you're seeing (if any)
4. **Screenshot of your OAuth consent screen** (if possible)
5. **Screenshot of your Authorized redirect URIs** (if possible)

Or if you've already created the credentials, just share:
- Your **Client ID** (safe to share)
- Your **production domain**
- The **exact error message** you're seeing

---

## 🚀 After Setup

Once configured, users will be able to:
1. Click "Continue with Google" on login/signup pages
2. Be redirected to Google for authentication
3. Grant permissions
4. Be automatically logged into your ASCAI platform
5. Have their account created/linked automatically

The system will:
- Create a new user account if email doesn't exist
- Link Google account to existing user if email matches
- Activate account immediately (Google emails are pre-verified)
- Extract name from Google profile

---

**Last Updated:** Based on django-allauth 0.57.0 and Google OAuth 2.0

