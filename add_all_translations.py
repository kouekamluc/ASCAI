#!/usr/bin/env python
"""
Comprehensive translation updater - extracts ALL strings from templates
and adds French and Italian translations for page content.
"""
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent

# Comprehensive French translations for ALL page content
FRENCH_TRANSLATIONS = {
    # Dashboard
    "Welcome,": "Bienvenue,",
    "Your personal dashboard overview": "Vue d'ensemble de votre tableau de bord personnel",
    "Membership Status": "Statut d'adhésion",
    "Status:": "Statut :",
    "Membership Number:": "Numéro d'adhésion :",
    "Category:": "Catégorie :",
    "Expiry Date:": "Date d'expiration :",
    "Total Events": "Total des événements",
    "All time registrations": "Inscriptions de tous temps",
    "Events Attended": "Événements assistés",
    "Completed events": "Événements terminés",
    "Upcoming Events": "Événements à venir",
    "Registered events": "Événements enregistrés",
    "Total Payments": "Total des paiements",
    "completed payments": "paiements effectués",
    "Activity Overview": "Aperçu de l'activité",
    "Event Participation Over Time": "Participation aux événements au fil du temps",
    "Payment History": "Historique des paiements",
    "Event Status Distribution": "Répartition du statut des événements",
    "Browse All": "Voir tout",
    "No upcoming events. Browse available events to register.": "Aucun événement à venir. Parcourez les événements disponibles pour vous inscrire.",
    "Recent News": "Actualités récentes",
    "View All": "Voir tout",
    "No news available at the moment.": "Aucune actualité disponible pour le moment.",
    "Recent Activity": "Activité récente",
    "No recent activity to display.": "Aucune activité récente à afficher.",
    "Quick Actions": "Actions rapides",
    "Edit Profile": "Modifier le profil",
    "Update your personal information": "Mettre à jour vos informations personnelles",
    "Browse Events": "Parcourir les événements",
    "View and register for upcoming events": "Voir et s'inscrire aux événements à venir",
    "View and upload documents": "Voir et télécharger des documents",
    "Job Board": "Tableau d'emplois",
    "Browse and apply for job opportunities": "Parcourir et postuler aux opportunités d'emploi",
    "Member Directory": "Répertoire des membres",
    "Connect with other members": "Se connecter avec d'autres membres",
    "Forums": "Forums",
    "Join discussions and share ideas": "Rejoindre les discussions et partager des idées",
    "Event Registrations": "Inscriptions aux événements",
    "Payments (€)": "Paiements (€)",
    
    # Landing page
    "Welcome to ASCAI": "Bienvenue à ASCAI",
    "Our Community": "Notre communauté",
    "Network": "Réseau",
    "Connect with fellow students and alumni": "Connectez-vous avec d'autres étudiants et anciens",
    "Participate in cultural and academic events": "Participez à des événements culturels et académiques",
    "Resources": "Ressources",
    "Support": "Soutien",
    "Get help and guidance from the community": "Obtenez de l'aide et des conseils de la communauté",
    
    # Events
    "Events": "Événements",
    "Calendar View": "Vue calendrier",
    "Manage Categories": "Gérer les catégories",
    "Search events...": "Rechercher des événements...",
    "Upcoming": "À venir",
    "Past": "Passé",
    "Search...": "Rechercher...",
    
    # News
    "News & Announcements": "Actualités et annonces",
    "Create Post": "Créer un article",
    
    # Jobs
    "Job Board": "Tableau d'emplois",
    "Job & Internship Board": "Tableau d'emplois et de stages",
    "Discover exciting career opportunities and internships": "Découvrez des opportunités de carrière et des stages passionnants",
    "Post a Job": "Publier un emploi",
    "Search jobs, companies, or keywords...": "Rechercher des emplois, entreprises ou mots-clés...",
    "Search jobs": "Rechercher des emplois",
    "Job type filter": "Filtre de type d'emploi",
    "Location (e.g., Rome, Italy)": "Localisation (ex. : Rome, Italie)",
    "Location filter": "Filtre de localisation",
    "Company name": "Nom de l'entreprise",
    "Company filter": "Filtre d'entreprise",
    "No jobs found": "Aucun emploi trouvé",
    
    # Common
    "View": "Voir",
    "Browse All": "Voir tout",
}

# Comprehensive Italian translations for ALL page content
ITALIAN_TRANSLATIONS = {
    # Dashboard
    "Welcome,": "Benvenuto,",
    "Your personal dashboard overview": "Panoramica della tua dashboard personale",
    "Membership Status": "Stato membro",
    "Status:": "Stato:",
    "Membership Number:": "Numero membro:",
    "Category:": "Categoria:",
    "Expiry Date:": "Data di scadenza:",
    "Total Events": "Totale eventi",
    "All time registrations": "Iscrizioni di tutti i tempi",
    "Events Attended": "Eventi partecipati",
    "Completed events": "Eventi completati",
    "Upcoming Events": "Eventi in arrivo",
    "Registered events": "Eventi registrati",
    "Total Payments": "Totale pagamenti",
    "completed payments": "pagamenti completati",
    "Activity Overview": "Panoramica attività",
    "Event Participation Over Time": "Partecipazione agli eventi nel tempo",
    "Payment History": "Cronologia pagamenti",
    "Event Status Distribution": "Distribuzione stato eventi",
    "Browse All": "Vedi tutto",
    "No upcoming events. Browse available events to register.": "Nessun evento in arrivo. Sfoglia gli eventi disponibili per registrarti.",
    "Recent News": "Notizie recenti",
    "View All": "Vedi tutto",
    "No news available at the moment.": "Nessuna notizia disponibile al momento.",
    "Recent Activity": "Attività recente",
    "No recent activity to display.": "Nessuna attività recente da visualizzare.",
    "Quick Actions": "Azioni rapide",
    "Edit Profile": "Modifica profilo",
    "Update your personal information": "Aggiorna le tue informazioni personali",
    "Browse Events": "Sfoglia eventi",
    "View and register for upcoming events": "Visualizza e registrati agli eventi in arrivo",
    "View and upload documents": "Visualizza e carica documenti",
    "Job Board": "Bacheca lavori",
    "Browse and apply for job opportunities": "Sfoglia e candidati alle opportunità di lavoro",
    "Member Directory": "Elenco membri",
    "Connect with other members": "Connettiti con altri membri",
    "Forums": "Forum",
    "Join discussions and share ideas": "Partecipa alle discussioni e condividi idee",
    "Event Registrations": "Iscrizioni eventi",
    "Payments (€)": "Pagamenti (€)",
    
    # Landing page
    "Welcome to ASCAI": "Benvenuto in ASCAI",
    "Our Community": "La nostra comunità",
    "Network": "Rete",
    "Connect with fellow students and alumni": "Connettiti con altri studenti e alumni",
    "Participate in cultural and academic events": "Partecipa a eventi culturali e accademici",
    "Resources": "Risorse",
    "Support": "Supporto",
    "Get help and guidance from the community": "Ottieni aiuto e guida dalla comunità",
    
    # Events
    "Events": "Eventi",
    "Calendar View": "Vista calendario",
    "Manage Categories": "Gestisci categorie",
    "Search events...": "Cerca eventi...",
    "Upcoming": "In arrivo",
    "Past": "Passato",
    "Search...": "Cerca...",
    
    # News
    "News & Announcements": "Notizie e annunci",
    "Create Post": "Crea articolo",
    
    # Jobs
    "Job Board": "Bacheca lavori",
    "Job & Internship Board": "Bacheca lavori e stage",
    "Discover exciting career opportunities and internships": "Scopri entusiasmanti opportunità di carriera e stage",
    "Post a Job": "Pubblica un lavoro",
    "Search jobs, companies, or keywords...": "Cerca lavori, aziende o parole chiave...",
    "Search jobs": "Cerca lavori",
    "Job type filter": "Filtro tipo lavoro",
    "Location (e.g., Rome, Italy)": "Posizione (es. Roma, Italia)",
    "Location filter": "Filtro posizione",
    "Company name": "Nome azienda",
    "Company filter": "Filtro azienda",
    "No jobs found": "Nessun lavoro trovato",
    
    # Common
    "View": "Vedi",
    "Browse All": "Vedi tutto",
}

def extract_all_trans_strings():
    """Extract all trans strings from templates."""
    templates_dir = BASE_DIR / "templates"
    all_strings = set()
    
    if templates_dir.exists():
        for template_file in templates_dir.rglob("*.html"):
            try:
                content = template_file.read_text(encoding='utf-8')
                # Match {% trans "..." %} and {% trans '...' %}
                matches = re.findall(r'{%\s*trans\s+["\']([^"\']+)["\']\s*%}', content)
                all_strings.update(matches)
                
                # Match blocktrans
                blocktrans_matches = re.findall(r'{%\s*blocktrans[^%]*%}(.*?){%\s*endblocktrans\s*%}', content, re.DOTALL)
                for match in blocktrans_matches:
                    # Extract text from blocktrans (simple extraction)
                    text_matches = re.findall(r'([A-Z][a-z]+(?:\s+[a-z]+)*)', match)
                    all_strings.update(text_matches)
            except Exception as e:
                print(f"Error reading {template_file}: {e}")
    
    return sorted(all_strings)

def update_po_file_advanced(po_file_path, translations):
    """Advanced .po file updater that handles all cases."""
    try:
        content = po_file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {po_file_path}: {e}")
        return False
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    updated_count = 0
    in_msgid = False
    in_msgstr = False
    current_msgid = ""
    msgid_lines = []
    msgstr_start_idx = None
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Start of msgid
        if stripped.startswith('msgid '):
            in_msgid = True
            in_msgstr = False
            current_msgid = ""
            msgid_lines = [line]
            msgstr_start_idx = None
            i += 1
            continue
        
        # Continuation of msgid (multiline)
        if in_msgid and (stripped.startswith('"') or stripped.startswith("'")):
            msgid_lines.append(line)
            # Extract text from quoted string
            match = re.search(r'["\']([^"\']*)["\']', line)
            if match:
                current_msgid += match.group(1)
            i += 1
            continue
        
        # Start of msgstr
        if stripped.startswith('msgstr '):
            in_msgstr = True
            msgstr_start_idx = i
            
            # Check if we have a translation for this msgid
            if current_msgid in translations:
                translation = translations[current_msgid]
                # Escape quotes
                translation = translation.replace('\\', '\\\\').replace('"', '\\"')
                
                # Write msgid lines
                new_lines.extend(msgid_lines)
                # Write msgstr
                new_lines.append(f'msgstr "{translation}"')
                updated_count += 1
                i += 1
                # Skip existing msgstr lines
                while i < len(lines) and (lines[i].strip().startswith('"') or lines[i].strip().startswith("'")):
                    i += 1
                in_msgid = False
                in_msgstr = False
                current_msgid = ""
                msgid_lines = []
                continue
            else:
                # No translation, keep original
                new_lines.extend(msgid_lines)
                in_msgid = False
                in_msgstr = False
                current_msgid = ""
                msgid_lines = []
        
        # Regular line
        if not in_msgid:
            new_lines.append(line)
        
        i += 1
    
    # Handle any remaining msgid
    if msgid_lines:
        new_lines.extend(msgid_lines)
    
    if updated_count > 0:
        new_content = '\n'.join(new_lines)
        po_file_path.write_text(new_content, encoding='utf-8')
        print(f"Updated {po_file_path} with {updated_count} translations")
        return True
    
    return False

def update_po_simple(po_file_path, translations):
    """Simple but effective .po file updater."""
    try:
        content = po_file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {po_file_path}: {e}")
        return False
    
    updated_count = 0
    
    # Pattern: msgid "text" followed by msgstr "text" or msgstr ""
    pattern = r'(msgid\s+"([^"]+)"\s*\nmsgstr\s+")[^"]*(")'
    
    def replace_func(match):
        nonlocal updated_count
        msgid_text = match.group(2)
        
        if msgid_text in translations:
            translation = translations[msgid_text]
            # Escape quotes in translation
            translation = translation.replace('\\', '\\\\').replace('"', '\\"')
            updated_count += 1
            return f'{match.group(1)}{translation}{match.group(3)}'
        return match.group(0)
    
    new_content = re.sub(pattern, replace_func, content)
    
    if updated_count > 0:
        po_file_path.write_text(new_content, encoding='utf-8')
        print(f"Updated {po_file_path} with {updated_count} translations")
        return True
    
    return False

def main():
    """Update French and Italian .po files with comprehensive translations."""
    print("Adding comprehensive page content translations...")
    
    # Merge with existing translations from add_translations_comprehensive.py
    # Import existing translations
    try:
        from add_translations_comprehensive import FRENCH_TRANSLATIONS as EXISTING_FR, ITALIAN_TRANSLATIONS as EXISTING_IT
        FRENCH_TRANSLATIONS.update(EXISTING_FR)
        ITALIAN_TRANSLATIONS.update(EXISTING_IT)
    except:
        pass
    
    # Update French translations
    fr_po = BASE_DIR / "locale" / "fr" / "LC_MESSAGES" / "django.po"
    if fr_po.exists():
        update_po_simple(fr_po, FRENCH_TRANSLATIONS)
    else:
        print(f"French .po file not found: {fr_po}")
    
    # Update Italian translations
    it_po = BASE_DIR / "locale" / "it" / "LC_MESSAGES" / "django.po"
    if it_po.exists():
        update_po_simple(it_po, ITALIAN_TRANSLATIONS)
    else:
        print(f"Italian .po file not found: {it_po}")
    
    print("\nDone! Now run compile_translations.py to compile .mo files")

if __name__ == "__main__":
    main()

