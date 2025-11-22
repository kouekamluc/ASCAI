# 🚀 QUICK FIX: Google OAuth redirect_uri_mismatch

## Your Production Domain is: [TELL ME YOUR DOMAIN]

I need to know your actual production domain to give you the exact commands.

---

## Option 1: Fix via Django Shell (Fastest)

**Run these commands, replacing `YOUR-DOMAIN` with your actual domain:**

```bash
python manage.py shell
```

Then in the shell:
```python
from django.contrib.sites.models import Site

site = Site.objects.get(id=1)
site.domain = 'YOUR-DOMAIN-HERE.onrender.com'  # ← REPLACE THIS
site.name = 'ASCAI Platform'
site.save()

print(f"✅ Updated to: {site.domain}")
```

**Example if your domain is `ascai.onrender.com`:**
```python
site.domain = 'ascai.onrender.com'
```

---

## Option 2: Fix via Django Admin (Easiest)

1. Go to: `https://YOUR-DOMAIN/admin/sites/site/`
2. Click on the site (ID=1)
3. Change **Domain name** from `example.com` to your actual domain
4. Save

---

## Step 2: Update Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your OAuth 2.0 Client ID
3. Scroll to **"Authorized redirect URIs"**
4. Add this EXACT URL (replace `YOUR-DOMAIN`):

```
https://YOUR-DOMAIN/accounts/google/login/callback/
```

**⚠️ IMPORTANT:**
- Must end with `/callback/` (trailing slash!)
- Must use `https://`
- No spaces before/after

**Example:**
```
https://ascai.onrender.com/accounts/google/login/callback/
```

5. Click **SAVE**

---

## That's It! ✅

After doing both steps:
1. Restart your app (if needed)
2. Try Google login again

---

## Still Need Help?

**Tell me your production domain and I'll give you exact commands!**

Common domains:
- `ascai.onrender.com` (Render default)
- `ascai.it` (custom domain)
- Something else?

