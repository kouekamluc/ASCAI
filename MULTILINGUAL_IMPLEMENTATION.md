# Multilingual Implementation Guide (English, French, Italian)

This document outlines the implementation of multilingual support (i18n/L10n) for the ASCAI SaaS platform, ensuring world-class UI/UX while supporting French and Italian localization.

## ✅ Implementation Status

### 1. Internationalization (i18n) Foundation ✅

- **Externalized Strings**: All user-facing text uses Django's `{% trans %}` and `{% blocktrans %}` tags
- **Translation Files**: `.po` files exist for English, French, and Italian in `locale/` directory
- **Locale Middleware**: `LocaleMiddleware` is configured in `settings.py`
- **Language Switcher**: Functional language switcher in navigation

### 2. Text Expansion Design ✅

The CSS has been updated to handle text expansion for French and Italian:

#### Buttons (+35% buffer)
- **Location**: `static/css/style.css` - `.btn` class
- **Implementation**: 
  - Increased horizontal padding from `1.5rem` to `2.36rem` (35% expansion)
  - `white-space: nowrap` to prevent text wrapping
  - `min-width: fit-content` for flexible sizing

#### Navigation Labels (+30% buffer)
- **Location**: `static/css/style.css` - `.navbar-nav a` class
- **Implementation**:
  - Increased horizontal padding from `1rem` to `1.3rem` (30% expansion)
  - `white-space: nowrap` to prevent wrapping
  - Flexible min-width

#### Form Labels (+25% buffer)
- **Location**: `static/css/style.css` - `.form-label` class
- **Implementation**:
  - Already top-aligned (`display: block`)
  - `width: 100%` with `word-wrap: break-word` for natural wrapping
  - No fixed widths that would break with longer text

#### Tooltips/Error Messages (+20% buffer)
- **Location**: `static/css/style.css` - `.form-hint` and `.field-errors` classes
- **Implementation**:
  - Dynamic height with `word-wrap: break-word`
  - Increased `line-height: 1.5-1.6` for better readability
  - Flexible containers

### 3. Locale-Aware Formatting ✅

#### Settings Configuration
- **File**: `config/settings.py`
- **Settings**:
  ```python
  USE_I18N = True
  USE_L10N = True  # Enable locale-aware formatting
  USE_THOUSAND_SEPARATOR = True
  DECIMAL_SEPARATOR = "."  # Default, locale-specific
  THOUSAND_SEPARATOR = ","  # Default, locale-specific
  ```

#### Date/Time Formatting
Django's `date` filter is locale-aware when `USE_L10N = True`. Templates use:
- `{{ date|date:"F d, Y" }}` - Will automatically format based on locale
- `{{ date|date:"g:i A" }}` - Time formatting with locale support

#### Number Formatting
For numbers, use `{% localize on %}` blocks:
```django
{% load l10n %}
{% localize on %}
    €{{ salary|floatformat:0 }}
{% endlocalize %}
```

### 4. Pluralization Support ✅

Pluralization is implemented using Django's `{% blocktrans %}` tag:

**Before (incorrect)**:
```django
{{ count }} {% trans "views" %}
```

**After (correct)**:
```django
{% blocktrans count count=views_count %}
    {{ count }} view
{% plural %}
    {{ count }} views
{% endblocktrans %}
```

**Updated Templates**:
- `templates/jobs/list.html` - Views and applications counts
- `templates/jobs/detail.html` - Views and applications counts
- `templates/news/list.html` - Post views
- `templates/news/detail.html` - Post views

### 5. Form Labels (Top-Aligned) ✅

All form labels are already top-aligned:
- Labels use `display: block` with `margin-bottom`
- Labels appear above input fields, not beside them
- This accommodates longer French/Italian labels without layout shifts

**Example**:
```django
<div class="form-group">
    <label for="{{ form.name.id_for_label }}" class="form-label">
        {% trans "Name" %} <span class="required">*</span>
    </label>
    {{ form.name }}
</div>
```

## 📋 Testing & Quality Assurance

### Pseudo-Localization Tool

A pseudo-localization utility has been created: `pseudo_localization.py`

**Usage**:
```bash
python pseudo_localization.py
```

**What it does**:
- Expands text by 30% (simulating French/Italian expansion)
- Adds non-Latin characters (á, é, í, ó, ú, ç, ñ)
- Wraps text in brackets `[...]`
- Creates `_pseudo` versions of templates and translation files

**How to test**:
1. Run the script to generate pseudo-localized files
2. Review the `_pseudo` files to see expanded text
3. Temporarily replace originals with pseudo versions (backup first!)
4. Test the UI for:
   - Text overflow
   - Button text wrapping
   - Navigation menu overflow
   - Form label alignment issues
   - Tooltip/error message overflow

### Manual Testing Checklist

- [ ] **Buttons**: Test all button labels in French/Italian
  - Check for text wrapping
  - Verify button widths accommodate longer text
  - Test at all responsive breakpoints

- [ ] **Navigation**: Test navigation menu in all languages
  - Check for horizontal scrolling
  - Verify menu items don't overlap
  - Test mobile menu layout

- [ ] **Forms**: Test all forms in French/Italian
  - Verify labels are top-aligned
  - Check for label text wrapping
  - Test form field alignment
  - Verify error messages display correctly

- [ ] **Dates/Numbers**: Test locale-aware formatting
  - Verify dates display in locale format (DD/MM/YYYY for FR/IT)
  - Check number formatting (thousands separator)
  - Test currency display (€ symbol placement)

- [ ] **Pluralization**: Test plural forms
  - Test with 0, 1, and 2+ items
  - Verify correct plural forms in French/Italian

## 🔧 Maintenance

### Adding New Translations

1. **Extract strings**:
   ```bash
   python extract_translations.py
   ```

2. **Edit translation files**:
   - `locale/fr/LC_MESSAGES/django.po` - French translations
   - `locale/it/LC_MESSAGES/django.po` - Italian translations

3. **Compile translations**:
   ```bash
   python compile_translations.py
   ```

### Best Practices

1. **Never concatenate strings**: Use `{% blocktrans %}` with placeholders
   ```django
   {% blocktrans with name=user.name %}
       Welcome, {{ name }}!
   {% endblocktrans %}
   ```

2. **Always use context**: Provide context for translators in `.po` files
   ```po
   #. Context: Button label
   msgid "Save"
   msgstr "Enregistrer"
   ```

3. **Test with real translations**: Use professional human translators, not machine translation for core UI strings

4. **Monitor text expansion**: Regularly run pseudo-localization tests

## 📝 Notes

- **Text Expansion**: French and Italian text can be 20-35% longer than English
- **Icons**: Use universally understood icons for constrained spaces (trash can = delete, pencil = edit)
- **Truncation**: Only use truncation (`...`) as a last resort for non-critical content
- **Responsive Design**: Test all breakpoints (mobile, tablet, desktop) in all languages

## 🎯 Next Steps

1. **Complete Translation Files**: Add remaining translations to `.po` files
2. **Linguistic Review**: Have native French and Italian speakers review all translations
3. **Functional Testing**: Test all workflows in French and Italian
4. **Performance Testing**: Ensure translation loading doesn't impact performance
5. **User Testing**: Conduct user testing with French and Italian speakers

## 📚 Resources

- [Django Internationalization Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [Django Localization Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/formatting/)
- [Translation Best Practices](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#pluralization)

