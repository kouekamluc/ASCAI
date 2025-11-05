# Form ID Duplicate Fix

## Problem
Multiple form field elements in the same form (or across different forms on the same page) can have the same `id` attribute value. This prevents browsers from correctly autofilling forms and violates HTML standards.

## Solution

### 1. JavaScript Automatic Fix
A JavaScript file (`static/js/form-id-fix.js`) automatically detects and fixes duplicate IDs on page load and after dynamic content updates (HTMX).

**How it works:**
- Scans all form fields (input, select, textarea) on page load
- Identifies duplicate IDs
- Generates unique IDs based on form context
- Updates associated labels and ARIA attributes
- Runs automatically after HTMX swaps

### 2. Template Tag (Optional)
A template tag is available for manual control:
```django
{% load form_helpers %}

<label for="{{ form.field|unique_id:'form1' }}">Label</label>
{{ form.field }}
```

## Implementation

The fix is automatically applied to all pages via `base.html`:
```html
<script src="{% static 'js/form-id-fix.js' %}"></script>
```

## Best Practices for Prevention

### In Views
When creating multiple forms on the same page, use prefixes:

```python
# In your view
form1 = MyForm(prefix='form1')
form2 = MyForm(prefix='form2')
```

### In Templates
When using multiple forms, ensure each has a unique identifier:

```django
<form id="main-form" method="post">
    {{ form1 }}
</form>

<form id="secondary-form" method="post">
    {{ form2 }}
</form>
```

## Testing

To verify the fix is working:
1. Open browser DevTools
2. Check Console for message: "Fixed X duplicate form field ID(s)"
3. Inspect form fields - all should have unique IDs
4. Test autofill functionality

## Browser Compatibility

- Works in all modern browsers
- Automatically handles:
  - Dynamic content (HTMX)
  - Multiple forms on same page
  - Forms without prefixes
  - Nested forms

