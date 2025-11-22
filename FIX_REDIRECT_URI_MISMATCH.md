# 🔴 FIX: redirect_uri_mismatch Error

## The Exact Problem

Google is receiving: `http://localhost:8000/accounts/google/login/callback/`  
But your Google Console doesn't have this EXACT URL → **Error 400**

---

## ✅ Step-by-Step Fix

### Step 1: Go to Google Cloud Console

1. Open: https://console.cloud.google.com/apis/credentials
2. Make sure you're in the **correct project** (the one with your OAuth credentials)
3. Click on your **OAuth 2.0 Client ID** (the one you created)

---

### Step 2: Find "Authorized redirect URIs"

Scroll down to the section labeled **"Authorized redirect URIs"**

---

### Step 3: Add the EXACT URL

1. Click **"+ ADD URI"** button
2. **Copy and paste this EXACT URL** (no modifications!):

```
http://localhost:8000/accounts/google/login/callback/
```

**⚠️ CRITICAL - Must be EXACT:**
- ✅ Starts with `http://` (NOT `https://`)
- ✅ `localhost:8000` (no `www`, no extra characters)
- ✅ Path: `/accounts/google/login/callback/`
- ✅ **Trailing slash at the end** (`/callback/` not `/callback`)
- ✅ No spaces before or after
- ✅ Port is `8000` (match your Django server port)

3. Click **"SAVE"** (bottom of the page)

---

### Step 4: Verify It Was Added

After saving, you should see in the list:
```
http://localhost:8000/accounts/google/login/callback/
```

**Double-check:**
- [ ] It's in the list
- [ ] No extra spaces
- [ ] Trailing slash is there
- [ ] Using `http://` not `https://`

---

### Step 5: Test Again

1. **Wait 1-2 minutes** (Google sometimes takes a moment to update)
2. Go to: http://localhost:8000/accounts/login/
3. Click **"Continue with Google"**
4. Should work now! ✅

---

## 🔍 Common Mistakes to Avoid

### ❌ Wrong Examples (Don't Use These!)

```
❌ https://localhost:8000/accounts/google/login/callback/  (wrong protocol)
❌ http://localhost/accounts/google/login/callback/        (missing port)
❌ http://localhost:8000/accounts/google/login/callback   (missing trailing slash)
❌ http://www.localhost:8000/accounts/google/login/callback/  (www not needed)
❌ http://127.0.0.1:8000/accounts/google/login/callback/   (use localhost, not 127.0.0.1)
❌ http://localhost:8000/accounts/google/login/callback/  (extra space at end)
```

### ✅ Correct (Use This!)

```
✅ http://localhost:8000/accounts/google/login/callback/
```

---

## 📸 Visual Guide

**In Google Console, it should look like this:**

```
Authorized redirect URIs
┌─────────────────────────────────────────────────────────┐
│ http://localhost:8000/accounts/google/login/callback/   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚨 Still Not Working?

### Check 1: Is the URL in the list?

- Go back to Google Console
- Check if `http://localhost:8000/accounts/google/login/callback/` is actually there
- If not, add it again and SAVE

### Check 2: Exact match?

- Copy the URL from Google Console
- Compare character-by-character with: `http://localhost:8000/accounts/google/login/callback/`
- They must be **identical**

### Check 3: Wait a bit

- Google sometimes takes 1-2 minutes to update
- Try again after waiting

### Check 4: Clear browser cache

- Sometimes browsers cache OAuth errors
- Try in incognito/private mode
- Or clear browser cache

### Check 5: Different port?

If your Django server runs on a different port (not 8000):

1. Check what port you're using:
   ```bash
   # When you run: python manage.py runserver
   # It shows: Starting development server at http://127.0.0.1:XXXX/
   ```

2. Update both:
   - Django Site domain: `localhost:XXXX` (your port)
   - Google Console URI: `http://localhost:XXXX/accounts/google/login/callback/`

---

## 🎯 Quick Checklist

Before testing again, verify:

- [ ] Google Console has: `http://localhost:8000/accounts/google/login/callback/`
- [ ] URL is EXACT (no typos, no extra spaces)
- [ ] Using `http://` (not `https://`)
- [ ] Trailing slash present: `/callback/`
- [ ] Clicked SAVE in Google Console
- [ ] Waited 1-2 minutes after saving
- [ ] Django server is running on port 8000
- [ ] Django Site domain is `localhost:8000`

---

## 💡 Pro Tip

You can have **multiple redirect URIs** in Google Console:
- `http://localhost:8000/accounts/google/login/callback/` (for local testing)
- `https://your-domain.com/accounts/google/login/callback/` (for production)

Just add both, and Google will accept whichever matches!

---

**After adding the exact URL and saving, try Google login again!** 🚀

