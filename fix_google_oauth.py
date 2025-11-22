"""
Script to fix Google OAuth redirect URI mismatch.
This script updates the Django Site domain to match your production domain.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site

def fix_site_domain(domain_name, site_name=None):
    """
    Update the Django Site domain for OAuth redirect URIs.
    
    Args:
        domain_name: Your production domain (e.g., 'ascai.onrender.com' or 'ascai.it')
        site_name: Display name (optional, defaults to domain_name)
    """
    site = Site.objects.get(id=1)
    
    print(f"Current Site Domain: {site.domain}")
    print(f"Current Site Name: {site.name}")
    print(f"\nUpdating to:")
    print(f"Site Domain: {domain_name}")
    print(f"Site Name: {site_name or domain_name}")
    
    site.domain = domain_name
    site.name = site_name or domain_name
    site.save()
    
    print(f"\n✅ Site updated successfully!")
    print(f"\n📋 Now update your Google Cloud Console:")
    print(f"1. Go to: https://console.cloud.google.com/apis/credentials")
    print(f"2. Click on your OAuth 2.0 Client ID")
    print(f"3. In 'Authorized redirect URIs', add:")
    print(f"   https://{domain_name}/accounts/google/login/callback/")
    print(f"\n⚠️  Important:")
    print(f"   - Must include trailing slash: /callback/")
    print(f"   - Must use https:// in production")
    print(f"   - Must match exactly (no extra spaces)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fix_google_oauth.py <your-domain> [site-name]")
        print("\nExample:")
        print("  python fix_google_oauth.py ascai.onrender.com")
        print("  python fix_google_oauth.py ascai.onrender.com 'ASCAI Platform'")
        print("\nOr run in Django shell:")
        print("  python manage.py shell")
        print("  >>> from django.contrib.sites.models import Site")
        print("  >>> site = Site.objects.get(id=1)")
        print("  >>> site.domain = 'ascai.onrender.com'")
        print("  >>> site.name = 'ASCAI Platform'")
        print("  >>> site.save()")
        sys.exit(1)
    
    domain = sys.argv[1]
    site_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_site_domain(domain, site_name)

