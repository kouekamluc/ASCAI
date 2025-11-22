"""
Check Google OAuth configuration for local testing.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings

# Check Site domain
site = Site.objects.get(id=1)
print(f"📍 Site Domain: {site.domain}")
print(f"📍 Site Name: {site.name}")

# Check Google OAuth credentials
client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
secret = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret']

print(f"\n🔑 Client ID: {'SET' if client_id else 'NOT SET'}")
if client_id:
    print(f"   Value: {client_id[:30]}..." if len(client_id) > 30 else f"   Value: {client_id}")

print(f"\n🔐 Secret: {'SET' if secret else 'NOT SET'}")
if secret:
    print(f"   Value: {'*' * min(len(secret), 20)}...")

# Expected callback URL
print(f"\n✅ Expected Callback URL:")
print(f"   http://{site.domain}/accounts/google/login/callback/")

# Check if this matches what should be in Google Console
print(f"\n📋 Make sure Google Console has this redirect URI:")
print(f"   http://localhost:8000/accounts/google/login/callback/")
print(f"\n⚠️  Important:")
print(f"   - Must use http:// (not https://) for localhost")
print(f"   - Must end with /callback/ (trailing slash)")
print(f"   - Port must be 8000 (or match your Django server port)")

