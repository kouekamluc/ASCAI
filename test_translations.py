#!/usr/bin/env python
"""
Test script to verify translations are working.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils.translation import activate, gettext as _
from django.conf import settings

print("=" * 60)
print("Translation System Diagnostic")
print("=" * 60)

# Check settings
print(f"\n1. Settings:")
print(f"   USE_I18N: {settings.USE_I18N}")
print(f"   USE_L10N: {settings.USE_L10N}")
print(f"   LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
print(f"   LANGUAGES: {settings.LANGUAGES}")
print(f"   LOCALE_PATHS: {settings.LOCALE_PATHS}")

# Check if .mo files exist
print(f"\n2. Translation Files:")
for lang_code, lang_name in settings.LANGUAGES:
    mo_path = settings.LOCALE_PATHS[0] / lang_code / "LC_MESSAGES" / "django.mo"
    exists = mo_path.exists()
    size = mo_path.stat().st_size if exists else 0
    print(f"   {lang_code} ({lang_name}): {'✓' if exists else '✗'} {mo_path}")
    if exists:
        print(f"      Size: {size} bytes")

# Test translations
print(f"\n3. Translation Tests:")
test_strings = ["Home", "Students", "Diaspora", "Resources", "Contact", "Dashboard"]

for lang_code, lang_name in settings.LANGUAGES:
    print(f"\n   Testing {lang_name} ({lang_code}):")
    activate(lang_code)
    for test_str in test_strings:
        translated = _(test_str)
        status = "✓" if translated != test_str or lang_code == "en" else "✗"
        print(f"      {status} '{test_str}' -> '{translated}'")

print("\n" + "=" * 60)
print("If translations show '✗', the .mo files may need to be recompiled.")
print("Run: python compile_translations.py")
print("=" * 60)

