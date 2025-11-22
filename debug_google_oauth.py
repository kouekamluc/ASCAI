"""
Debug script to see exactly what redirect URI django-allauth is sending to Google.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from django.conf import settings
from django.test import RequestFactory
from allauth.socialaccount.providers.google.views import oauth2_login

# Get current site
site = Site.objects.get(id=1)
print(f"📍 Current Site Domain: {site.domain}\n")

# Create a mock request to see what URL would be generated
factory = RequestFactory()
request = factory.get('/accounts/google/login/')
request.META['HTTP_HOST'] = site.domain

# Try to get the redirect URI that would be sent
try:
    from allauth.socialaccount.providers.google.provider import GoogleProvider
    from allauth.socialaccount.helpers import complete_social_login
    
    # Get the provider
    provider = GoogleProvider(request)
    
    # Build the callback URL
    callback_url = f"http://{site.domain}/accounts/google/login/callback/"
    
    print(f"✅ Expected Callback URL Django will send:")
    print(f"   {callback_url}\n")
    
    print(f"📋 This EXACT URL must be in Google Console:")
    print(f"   {callback_url}\n")
    
    print(f"⚠️  Common Issues:")
    print(f"   1. Missing in Google Console → Add it!")
    print(f"   2. Wrong protocol → Must be http:// (not https://) for localhost")
    print(f"   3. Missing trailing slash → Must end with /callback/")
    print(f"   4. Wrong port → Must be :8000 (or your Django port)")
    print(f"   5. Extra spaces → Copy-paste exactly, no spaces")
    
except Exception as e:
    print(f"Could not determine exact URL: {e}")
    print(f"\nBut based on Site domain, it should be:")
    print(f"http://{site.domain}/accounts/google/login/callback/")

