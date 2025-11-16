# Translation Troubleshooting Guide

## Issue: Translations Not Working

If translations are not working, follow these steps:

### 1. Verify .mo Files Exist
The compiled translation files (.mo) must exist:
- `locale/fr/LC_MESSAGES/django.mo`
- `locale/it/LC_MESSAGES/django.mo`
- `locale/en/LC_MESSAGES/django.mo`

**Solution**: Run `python compile_translations.py` to compile .po files to .mo files.

### 2. Restart Django Server
Django caches translation files. After compiling .mo files, you MUST restart the Django development server.

**Solution**: 
- Stop the server (Ctrl+C)
- Start it again: `python manage.py runserver`

### 3. Clear Browser Cache
Your browser may have cached the old translations.

**Solution**: 
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Or clear browser cache

### 4. Verify Settings
Check that these are configured in `config/settings.py`:

```python
USE_I18N = True
USE_L10N = True

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("it", _("Italian")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]
```

And in `MIDDLEWARE`:
```python
"django.middleware.locale.LocaleMiddleware",  # Must be after SessionMiddleware
```

### 5. Verify Language Switcher
The language switcher should submit a POST request to `/i18n/setlang/`.

**Check**: Open browser developer tools (F12) → Network tab → Change language → Verify POST request to `/i18n/setlang/`

### 6. Test Translation
To test if translations are working:

1. Go to the site
2. Change language using the language switcher
3. Check if URL changes (e.g., `/fr/` prefix appears)
4. Check if text changes

### 7. Check for Translation Tags
All user-facing strings must be wrapped in `{% trans %}` tags in templates.

### 8. Verify .po Files
Check that .po files have translations (not empty msgstr):

```bash
# Check French translations
grep -A 1 'msgid "Home"' locale/fr/LC_MESSAGES/django.po
```

Should show:
```
msgid "Home"
msgstr "Accueil"
```

NOT:
```
msgid "Home"
msgstr "Home"  # or msgstr ""
```

## Quick Fix Commands

```bash
# 1. Recompile translations
python compile_translations.py

# 2. Restart Django server
# Stop current server (Ctrl+C), then:
python manage.py runserver

# 3. Clear Django cache (if using cache)
python manage.py clear_cache  # if available
```

## Common Issues

### Issue: Language switcher doesn't change language
**Cause**: LocaleMiddleware not in MIDDLEWARE or in wrong position
**Fix**: Ensure `LocaleMiddleware` is after `SessionMiddleware` in MIDDLEWARE

### Issue: Some strings translate, others don't
**Cause**: Missing `{% trans %}` tags or empty msgstr in .po files
**Fix**: Add `{% trans %}` tags and fill in translations in .po files

### Issue: Translations work after restart but stop working
**Cause**: .mo files were deleted or corrupted
**Fix**: Recompile with `python compile_translations.py`

### Issue: Language changes but page doesn't reload
**Cause**: JavaScript issue or form not submitting
**Fix**: Check browser console for errors, verify language switcher form

