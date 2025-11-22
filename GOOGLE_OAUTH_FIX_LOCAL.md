# ✅ Quick Fix: Google OAuth Local Testing

## Current Status

✅ **Site Domain:** `localhost:8000` (correct!)  
✅ **Client ID:** SET  
❌ **Client Secret:** NOT SET ⚠️

---

## 🔧 Fix: Add Client Secret

You need to add the `GOOGLE_OAUTH_CLIENT_SECRET` to your `.env` file.

### Step 1: Get Your Client Secret from Google Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click on your **OAuth 2.0 Client ID**
3. Copy the **Client Secret** (starts with `GOCSPX-...`)
4. ⚠️ **Important:** This is only shown once, so save it securely!

### Step 2: Add to Your .env File

Open your `.env` file (in the root of your project) and add:

```bash
GOOGLE_OAUTH_CLIENT_ID=378723021932-rrptqo2stn8taba2k...your-full-client-id
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-client-secret-here
```

**Replace:**
- `378723021932-rrptqo2stn8taba2k...your-full-client-id` with your full Client ID
- `GOCSPX-your-client-secret-here` with your actual Client Secret

**Example:**
```bash
GOOGLE_OAUTH_CLIENT_ID=378723021932-rrptqo2stn8taba2kabc123def456.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-abc123def456xyz789
```

### Step 3: Restart Django Server

After adding the secret, **restart your Django server**:

```bash
# Stop the server (Ctrl+C)
# Then start again:
python manage.py runserver
```

### Step 4: Verify

Run the check script again:

```bash
python check_google_oauth.py
```

You should now see:
```
🔑 Client ID: SET
🔐 Secret: SET  ✅
```

---

## 📋 Complete Checklist

- [ ] **Site Domain:** `localhost:8000` ✅ (already done!)
- [ ] **Client ID:** In `.env` file ✅ (already set!)
- [ ] **Client Secret:** In `.env` file ⚠️ (need to add this!)
- [ ] **Google Console Redirect URI:** `http://localhost:8000/accounts/google/login/callback/` (need to verify)
- [ ] **Django server restarted** after adding secret

---

## 🎯 What You Need to Do

1. **Add to `.env` file:**
   ```bash
   GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-secret-here
   ```

2. **Verify Google Console has:**
   ```
   http://localhost:8000/accounts/google/login/callback/
   ```

3. **Restart Django server**

4. **Test again!**

---

## 💡 Quick Reference

**Your .env file should have:**
```bash
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=378723021932-rrptqo2stn8taba2k...your-full-id
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-secret
```

**Your Google Console should have:**
```
http://localhost:8000/accounts/google/login/callback/
```

---

After adding the secret and restarting, try Google login again! 🚀

