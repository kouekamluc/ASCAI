# Fix Google OAuth redirect_uri_mismatch Error

## 🔴 The Problem

You're getting: **Error 400: redirect_uri_mismatch**

This happens because:
1. Django's Site domain is set to `example.com` (default)
2. django-allauth builds the callback URL using this domain
3. Google receives: `https://example.com/accounts/google/login/callback/`
4. But your Google Console only has: `https://your-domain.com/accounts/google/login/callback/`
5. They don't match → **Error!**

---

## ✅ Quick Fix (3 Steps)

### Step 1: Update Django Site Domain

**Option A: Using the Fix Script (Recommended)**

```bash
python fix_google_oauth.py your-domain.com "ASCAI Platform"
```

Replace `your-domain.com` with your actual domain (e.g., `ascai.onrender.com`)

**Option B: Using Django Shell**

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site

site = Site.objects.get(id=1)
site.domain = 'ascai.onrender.com'  # YOUR ACTUAL DOMAIN
site.name = 'ASCAI Platform'
site.save()

print(f"✅ Site updated: {site.domain}")
```

**Option C: Using Django Admin**

1. Go to: `https://your-domain.com/admin/sites/site/`
2. Click on the site (usually ID=1)
3. Change:
   - **Domain name:** `ascai.onrender.com` (YOUR ACTUAL DOMAIN)
   - **Display name:** `ASCAI Platform`
4. Click **Save**

---

### Step 2: Add Redirect URI to Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to: **APIs & Services** → **Credentials**
4. Click on your **OAuth 2.0 Client ID**
5. Scroll to **"Authorized redirect URIs"**
6. Click **"+ ADD URI"**
7. Add this **EXACT** URL:

```
https://your-domain.com/accounts/google/login/callback/
```

**Replace `your-domain.com` with your actual domain!**

**⚠️ Critical Notes:**
- ✅ Must end with `/callback/` (trailing slash!)
- ✅ Must use `https://` (not `http://`)
- ✅ No trailing spaces
- ✅ Match exactly what you set in Django Site domain

**Examples:**
```
✅ https://ascai.onrender.com/accounts/google/login/callback/
✅ https://ascai.it/accounts/google/login/callback/
❌ https://ascai.onrender.com/accounts/google/login/callback (missing trailing slash)
❌ http://ascai.onrender.com/accounts/google/login/callback/ (should be https)
```

8. Click **"SAVE"**

---

### Step 3: Test

1. Restart your Django application
2. Go to: `https://your-domain.com/accounts/login/`
3. Click **"Continue with Google"**
4. Should now work! ✅

---

## 🔍 Verify Your Current Configuration

### Check Django Site Domain

```bash
python manage.py shell -c "from django.contrib.sites.models import Site; site = Site.objects.get(id=1); print(f'Domain: {site.domain}'); print(f'Name: {site.name}')"
```

### Check What Redirect URI Django is Sending

Add this temporarily to see the exact URL:

```python
# In your views or shell
from allauth.socialaccount.providers.google.views import oauth2_login
from django.contrib.sites.shortcuts import get_current_site

site = get_current_site(request)
print(f"Site domain: {site.domain}")
print(f"Callback URL would be: https://{site.domain}/accounts/google/login/callback/")
```

---

## 📋 Complete Checklist

- [ ] Django Site domain updated (not `example.com`)
- [ ] Redirect URI added to Google Console (exact match)
- [ ] Redirect URI ends with `/callback/` (trailing slash)
- [ ] Using `https://` (not `http://`) in production
- [ ] App restarted after changes
- [ ] Tested the login flow

---

## 🎯 Exact Redirect URIs to Add in Google Console

Based on your setup, add **all** of these:

**For Development:**
```
http://localhost:8000/accounts/google/login/callback/
```

**For Production:**
```
https://ascai.onrender.com/accounts/google/login/callback/
```

**If you have a custom domain:**
```
https://ascai.it/accounts/google/login/callback/
https://www.ascai.it/accounts/google/login/callback/
```

---

## 🚨 Common Mistakes

1. **Wrong domain in Django Site** → Update to match your actual domain
2. **Missing trailing slash** → Must be `/callback/` not `/callback`
3. **Using http:// in production** → Must use `https://`
4. **Typo in redirect URI** → Copy-paste from error message to verify
5. **Forgetting to save** → Changes don't take effect until saved
6. **Not restarting app** → Django needs restart to pick up Site changes

---

## 💡 What's Your Domain?

Please tell me your actual production domain, and I'll give you the exact commands to run!

Example domains:
- `ascai.onrender.com` (Render default)
- `ascai.it` (custom domain)
- `www.ascai.it` (custom domain with www)

Once you share your domain, I can provide:
1. Exact Django shell command
2. Exact redirect URI to add in Google Console
3. Exact environment variable updates

