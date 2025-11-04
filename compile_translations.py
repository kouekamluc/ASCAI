#!/usr/bin/env python
"""
Compile .po files to .mo files without requiring gettext tools.
Uses polib if available, otherwise creates minimal .mo files.
"""
import os
import struct
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOCALE_DIR = BASE_DIR / "locale"

def compile_po_to_mo(po_file_path):
    """Compile a .po file to .mo format."""
    mo_file_path = po_file_path.with_suffix('.mo')
    
    # Try using polib if available
    try:
        import polib
        po = polib.pofile(str(po_file_path))
        po.save_as_mofile(str(mo_file_path))
        print(f"Compiled {po_file_path} -> {mo_file_path} (using polib)")
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"Error using polib: {e}, falling back to manual compilation")
    
    # Fallback: manual compilation
    # Read the .po file
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the .po file (handle multiline strings)
    entries = {}
    lines = content.split('\n')
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('msgid "'):
            # Save previous entry
            if current_msgid is not None and current_msgstr is not None:
                entries[current_msgid] = current_msgstr
            # Start new entry
            current_msgid = stripped[7:-1].replace('\\"', '"').replace('\\\\', '\\')
            current_msgstr = ""
            in_msgid = True
            in_msgstr = False
        elif stripped.startswith('msgstr "'):
            in_msgid = False
            in_msgstr = True
            if current_msgstr == "":
                current_msgstr = stripped[8:-1].replace('\\"', '"').replace('\\\\', '\\')
        elif stripped.startswith('"') and (in_msgid or in_msgstr):
            # Continuation line
            cont = stripped[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            if in_msgid:
                current_msgid += cont
            elif in_msgstr:
                current_msgstr += cont
        elif not stripped or stripped.startswith('#'):
            # Empty line or comment - reset state
            in_msgid = False
            in_msgstr = False
    
    # Add last entry
    if current_msgid is not None and current_msgstr is not None:
        entries[current_msgid] = current_msgstr
    
    # Write .mo file (binary format)
    # MO file format: magic number + revision + num_strings + offset_table + strings
    with open(mo_file_path, 'wb') as f:
        # Magic number (0x950412de for little-endian)
        f.write(struct.pack('<I', 0x950412de))
        # Version (0)
        f.write(struct.pack('<I', 0))
        # Number of strings
        num_strings = len(entries) + 1  # +1 for header
        f.write(struct.pack('<I', num_strings))
        # Offset to table of original strings
        table_offset = 28  # Header size
        f.write(struct.pack('<I', table_offset))
        # Offset to table of translated strings
        f.write(struct.pack('<I', table_offset + num_strings * 8))
        # Length and offset of strings
        strings_data = b''
        offsets = []
        current_offset = table_offset + num_strings * 16
        
        # Header entry (empty msgid, msgstr is the file header)
        header_msg = ""
        offsets.append((len(header_msg), current_offset))
        strings_data += header_msg.encode('utf-8') + b'\x00'
        current_offset += len(header_msg) + 1
        
        # Regular entries
        for msgid, msgstr in entries.items():
            offsets.append((len(msgid.encode('utf-8')), current_offset))
            strings_data += msgid.encode('utf-8') + b'\x00'
            current_offset += len(msgid.encode('utf-8')) + 1
        
        # Write offset table for original strings
        for length, offset in offsets:
            f.write(struct.pack('<I', length))
            f.write(struct.pack('<I', offset))
        
        # Write offset table for translated strings
        translated_offsets = []
        translated_offset = current_offset
        for msgid, msgstr in entries.items():
            translated_offsets.append((len(msgstr.encode('utf-8')), translated_offset))
            translated_offset += len(msgstr.encode('utf-8')) + 1
        
        # Header translation offset
        header_str = ""
        translated_offsets.insert(0, (len(header_str.encode('utf-8')), translated_offset))
        translated_offset += len(header_str.encode('utf-8')) + 1
        
        for length, offset in translated_offsets:
            f.write(struct.pack('<I', length))
            f.write(struct.pack('<I', offset))
        
        # Write translated strings
        strings_data += header_str.encode('utf-8') + b'\x00'
        for msgid, msgstr in entries.items():
            strings_data += msgstr.encode('utf-8') + b'\x00'
        
        # Write all strings
        f.write(strings_data)
    
    print(f"Compiled {po_file_path} -> {mo_file_path}")

def compile_all():
    """Compile all .po files in locale directory."""
    for lang_dir in LOCALE_DIR.iterdir():
        if lang_dir.is_dir():
            po_file = lang_dir / "LC_MESSAGES" / "django.po"
            if po_file.exists():
                try:
                    compile_po_to_mo(po_file)
                except Exception as e:
                    print(f"Error compiling {po_file}: {e}")

if __name__ == "__main__":
    print("Compiling translation files...")
    compile_all()
    print("Done!")

