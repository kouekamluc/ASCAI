#!/usr/bin/env python
"""
Extract all translatable strings from templates and Python files.
"""
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent

def extract_from_template(file_path):
    """Extract trans strings from Django template."""
    strings = []
    try:
        content = file_path.read_text(encoding='utf-8')
        # Match {% trans "..." %} and {% trans '...' %}
        matches = re.findall(r'{%\s*trans\s+["\']([^"\']+)["\']\s*%}', content)
        strings.extend(matches)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return strings

def extract_from_python(file_path):
    """Extract translatable strings from Python file."""
    strings = []
    try:
        content = file_path.read_text(encoding='utf-8')
        # Match _("...") and _('...')
        matches = re.findall(r'_\s*\(\s*["\']([^"\']+)["\']\s*\)', content)
        strings.extend(matches)
        # Match gettext_lazy("...")
        matches = re.findall(r'gettext_lazy\s*\(\s*["\']([^"\']+)["\']\s*\)', content)
        strings.extend(matches)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return strings

def find_all_strings():
    """Find all translatable strings in the project."""
    all_strings = set()
    
    # Extract from templates
    templates_dir = BASE_DIR / "templates"
    if templates_dir.exists():
        for template_file in templates_dir.rglob("*.html"):
            strings = extract_from_template(template_file)
            all_strings.update(strings)
    
    # Extract from Python files
    apps_dir = BASE_DIR / "apps"
    if apps_dir.exists():
        for py_file in apps_dir.rglob("*.py"):
            strings = extract_from_python(py_file)
            all_strings.update(strings)
    
    # Extract from config
    config_dir = BASE_DIR / "config"
    if config_dir.exists():
        for py_file in config_dir.rglob("*.py"):
            strings = extract_from_python(py_file)
            all_strings.update(strings)
    
    return sorted(list(all_strings))

def update_po_files():
    """Update .po files with extracted strings."""
    strings = find_all_strings()
    print(f"Found {len(strings)} translatable strings")
    
    # Language translations
    translations = {
        "fr": get_french_translations(),
        "it": get_italian_translations(),
    }
    
    for lang_code in ["en", "fr", "it"]:
        update_po_file(lang_code, strings, translations.get(lang_code, {}))

def update_po_file(lang_code, strings, translation_dict):
    """Update a .po file with new strings."""
    from datetime import datetime
    
    locale_path = BASE_DIR / "locale" / lang_code / "LC_MESSAGES"
    po_file = locale_path / "django.po"
    
    # Read existing file if it exists
    existing_entries = {}
    if po_file.exists():
        content = po_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        current_msgid = None
        current_msgstr = None
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('msgid "'):
                if current_msgid is not None:
                    existing_entries[current_msgid] = current_msgstr
                current_msgid = line_stripped[7:-1]
                current_msgstr = ""
            elif line_stripped.startswith('msgstr "'):
                current_msgstr = line_stripped[8:-1]
            elif line_stripped.startswith('"') and current_msgstr is not None:
                current_msgstr += line_stripped[1:-1]
        
        if current_msgid is not None:
            existing_entries[current_msgid] = current_msgstr
    
    # Create new content
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M%z")
    
    header = f'''# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: ASCAI Platform 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: {date_str}\\n"
"PO-Revision-Date: {date_str}\\n"
"Last-Translator: \\n"
"Language-Team: {lang_code}\\n"
"Language: {lang_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''
    
    content = header
    for string in strings:
        if not string.strip():
            continue
        # Escape quotes
        escaped_string = string.replace('\\', '\\\\').replace('"', '\\"')
        content += f'msgid "{escaped_string}"\n'
        
        if lang_code == "en":
            msgstr = string
        else:
            msgstr = translation_dict.get(string, string)
        
        escaped_msgstr = msgstr.replace('\\', '\\\\').replace('"', '\\"')
        content += f'msgstr "{escaped_msgstr}"\n\n'
    
    po_file.write_text(content, encoding='utf-8')
    print(f"Updated {po_file}")

def get_french_translations():
    """Get French translations for common strings."""
    return {
        "Dashboard": "Tableau de bord",
        "Admin": "Administration",
        "Events": "Événements",
        "News": "Actualités",
        "Forum": "Forum",
        "Documents": "Documents",
        "Jobs": "Emplois",
        "Members": "Membres",
        "Profile": "Profil",
        "Logout": "Déconnexion",
        "Login": "Connexion",
        "Register": "S'inscrire",
        "Welcome to ASCAI": "Bienvenue à ASCAI",
        "Association of Cameroonian Students in Lazio, Italy": "Association des étudiants camerounais du Latium, Italie",
        "Connecting Cameroonian students in the Lazio region, fostering community, and supporting academic excellence.": "Connecter les étudiants camerounais de la région du Latium, favoriser la communauté et soutenir l'excellence académique.",
        "Join Us": "Rejoignez-nous",
        "Go to Dashboard": "Aller au tableau de bord",
        "View News": "Voir les actualités",
        "Submit": "Soumettre",
        "Cancel": "Annuler",
        "Edit": "Modifier",
        "Delete": "Supprimer",
        "Save": "Enregistrer",
        "Update": "Mettre à jour",
        "Create": "Créer",
        "Search": "Rechercher",
        "Filter": "Filtrer",
        "Clear": "Effacer",
        "Previous": "Précédent",
        "Next": "Suivant",
        "Page": "Page",
        "of": "sur",
        "Title": "Titre",
        "Description": "Description",
        "Content": "Contenu",
        "Category": "Catégorie",
        "Tags": "Tags",
        "Name": "Nom",
        "Email": "Email",
        "Password": "Mot de passe",
    }

def get_italian_translations():
    """Get Italian translations for common strings."""
    return {
        "Dashboard": "Dashboard",
        "Admin": "Amministrazione",
        "Events": "Eventi",
        "News": "Notizie",
        "Forum": "Forum",
        "Documents": "Documenti",
        "Jobs": "Lavori",
        "Members": "Membri",
        "Profile": "Profilo",
        "Logout": "Disconnetti",
        "Login": "Accedi",
        "Register": "Registrati",
        "Welcome to ASCAI": "Benvenuto in ASCAI",
        "Association of Cameroonian Students in Lazio, Italy": "Associazione degli Studenti Camerunensi nel Lazio, Italia",
        "Connecting Cameroonian students in the Lazio region, fostering community, and supporting academic excellence.": "Collegare gli studenti camerunensi nella regione del Lazio, favorire la comunità e sostenere l'eccellenza accademica.",
        "Join Us": "Unisciti a noi",
        "Go to Dashboard": "Vai alla Dashboard",
        "View News": "Vedi le notizie",
        "Submit": "Invia",
        "Cancel": "Annulla",
        "Edit": "Modifica",
        "Delete": "Elimina",
        "Save": "Salva",
        "Update": "Aggiorna",
        "Create": "Crea",
        "Search": "Cerca",
        "Filter": "Filtra",
        "Clear": "Cancella",
        "Previous": "Precedente",
        "Next": "Successivo",
        "Page": "Pagina",
        "of": "di",
        "Title": "Titolo",
        "Description": "Descrizione",
        "Content": "Contenuto",
        "Category": "Categoria",
        "Tags": "Tag",
        "Name": "Nome",
        "Email": "Email",
        "Password": "Password",
    }

if __name__ == "__main__":
    print("Extracting translatable strings...")
    update_po_files()
    print("Done! Run compile_translations.py to compile .mo files")






