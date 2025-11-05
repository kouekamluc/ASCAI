#!/usr/bin/env python
"""
Pseudo-localization utility for testing text expansion.

This script replaces English text with expanded pseudo-localized text
that is 30% longer and contains non-Latin characters to test if the UI
can handle text expansion and special characters.
"""

import re
from pathlib import Path

# Character mapping for pseudo-localization
CHAR_MAP = {
    'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú',
    'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú',
    'c': 'ç', 'C': 'Ç',
    'n': 'ñ', 'N': 'Ñ',
    ' ': '  ',  # Double spaces to simulate expansion
}

# Expansion markers
PREFIX = '['
SUFFIX = ']'

def expand_text(text, expansion_factor=1.3):
    """Expand text by the given factor and add pseudo-localized characters."""
    # Add expansion markers
    expanded = PREFIX + text + SUFFIX
    
    # Apply character transformations
    result = ''
    for char in expanded:
        if char in CHAR_MAP:
            result += CHAR_MAP[char]
        else:
            result += char
    
    # Add extra characters to reach expansion factor
    original_length = len(text)
    target_length = int(original_length * expansion_factor)
    current_length = len(result)
    
    if current_length < target_length:
        # Add extra characters (spaces and punctuation)
        extra_needed = target_length - current_length
        result += ' ' * (extra_needed // 2)
        if extra_needed % 2:
            result += '~'
    
    return result

def pseudo_localize_template(template_path):
    """Pseudo-localize a Django template file."""
    try:
        content = template_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {template_path}: {e}")
        return False
    
    # Pattern to match {% trans "..." %} tags
    trans_pattern = r'{%\s*trans\s+["\']([^"\']+)["\']\s*%}'
    
    def replace_trans(match):
        original_text = match.group(1)
        expanded = expand_text(original_text)
        return f'{{% trans "{expanded}" %}}'
    
    # Replace trans tags
    new_content = re.sub(trans_pattern, replace_trans, content)
    
    # Pattern to match {% blocktrans %}...{% endblocktrans %}
    # This is more complex and would require a full parser
    # For now, we'll just handle simple trans tags
    
    if new_content != content:
        # Write to a test file
        test_path = template_path.parent / f"{template_path.stem}_pseudo{template_path.suffix}"
        test_path.write_text(new_content, encoding='utf-8')
        print(f"Created pseudo-localized version: {test_path}")
        return True
    
    return False

def pseudo_localize_po_file(po_path):
    """Pseudo-localize a .po translation file."""
    try:
        content = po_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {po_path}: {e}")
        return False
    
    # Pattern to match msgstr entries
    msgstr_pattern = r'msgstr\s+"([^"]+)"'
    
    def replace_msgstr(match):
        original_text = match.group(1)
        if original_text:  # Only expand non-empty strings
            expanded = expand_text(original_text)
            return f'msgstr "{expanded}"'
        return match.group(0)
    
    new_content = re.sub(msgstr_pattern, replace_msgstr, content)
    
    if new_content != content:
        test_path = po_path.parent / f"{po_path.stem}_pseudo{po_path.suffix}"
        test_path.write_text(new_content, encoding='utf-8')
        print(f"Created pseudo-localized version: {test_path}")
        return True
    
    return False

def main():
    """Run pseudo-localization on templates and translation files."""
    base_dir = Path(__file__).resolve().parent
    
    print("Pseudo-localization Test")
    print("=" * 50)
    print("This will create test files with expanded text to check layout.")
    print("Files will be created with '_pseudo' suffix.\n")
    
    # Process templates
    templates_dir = base_dir / "templates"
    if templates_dir.exists():
        template_count = 0
        for template_file in templates_dir.rglob("*.html"):
            if pseudo_localize_template(template_file):
                template_count += 1
        print(f"\nProcessed {template_count} template files.")
    
    # Process translation files
    locale_dir = base_dir / "locale"
    if locale_dir.exists():
        po_count = 0
        for po_file in locale_dir.rglob("*.po"):
            if pseudo_localize_po_file(po_file):
                po_count += 1
        print(f"Processed {po_count} translation files.")
    
    print("\n" + "=" * 50)
    print("Pseudo-localization complete!")
    print("\nTo test:")
    print("1. Copy the _pseudo files to replace originals (backup first!)")
    print("2. Or manually review the _pseudo files to see expansion")
    print("3. Check for layout breaks, text overflow, and overlapping elements")

if __name__ == "__main__":
    main()

