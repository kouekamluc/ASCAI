#!/usr/bin/env python
"""
Comprehensive translation updater for .po files.
Properly parses .po files and adds French and Italian translations.
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Extended French translations
FRENCH_TRANSLATIONS = {
    "Dashboard": "Tableau de bord",
    "Admin": "Administration",
    "Events": "Événements",
    "News": "Actualités",
    "Forum": "Forum",
    "Documents": "Documents",
    "Jobs": "Emplois",
    "Members": "Membres",
    "Messages": "Messages",
    "Profile": "Profil",
    "Logout": "Déconnexion",
    "Login": "Connexion",
    "Register": "S'inscrire",
    "Save": "Enregistrer",
    "Cancel": "Annuler",
    "Edit": "Modifier",
    "Delete": "Supprimer",
    "Submit": "Soumettre",
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
    "ASCAI - Association of Cameroonian Students in Lazio": "ASCAI - Association des étudiants camerounais du Latium",
    "ASCAI - Association of Cameroonian Students in Lazio, Italy": "ASCAI - Association des étudiants camerounais du Latium, Italie",
    "Welcome to ASCAI": "Bienvenue à ASCAI",
    "Association of Cameroonian Students in Lazio, Italy": "Association des étudiants camerounais du Latium, Italie",
    "Connecting Cameroonian students in the Lazio region, fostering community, and supporting academic excellence.": "Connecter les étudiants camerounais de la région du Latium, favoriser la communauté et soutenir l'excellence académique.",
    "Join Us": "Rejoignez-nous",
    "Go to Dashboard": "Aller au tableau de bord",
    "View News": "Voir les actualités",
    "Account Activated": "Compte activé",
    "Your account has been successfully activated!": "Votre compte a été activé avec succès !",
    "Activate Account": "Activer le compte",
    "Activate your ASCAI account": "Activez votre compte ASCAI",
    "Activation Link Invalid": "Lien d'activation invalide",
    "Please check your email and click the activation link to activate your account.": "Veuillez vérifier votre e-mail et cliquer sur le lien d'activation pour activer votre compte.",
    "Back to Login": "Retour à la connexion",
    "Already have an account? Login here": "Vous avez déjà un compte ? Connectez-vous ici",
    "Don't have an account? Register here": "Vous n'avez pas de compte ? Inscrivez-vous ici",
    "Change Password": "Changer le mot de passe",
    "Back to Profile": "Retour au profil",
    "No events found.": "Aucun événement trouvé.",
    "No news posts found.": "Aucun article d'actualité trouvé.",
    "No jobs found": "Aucun emploi trouvé",
    "Job Title": "Titre du poste",
    "Company Name": "Nom de l'entreprise",
    "Location": "Localisation",
    "Job Type": "Type d'emploi",
    "Salary Range": "Échelle salariale",
    "From": "À partir de",
    "Up to": "Jusqu'à",
    "Deadline": "Date limite",
    "Application Deadline": "Date limite de candidature",
    "Job Description": "Description du poste",
    "Requirements": "Exigences",
    "Posted by": "Publié par",
    "Apply Now": "Postuler maintenant",
    "You have already applied to this job.": "Vous avez déjà postulé à cet emploi.",
    "View My Applications": "Voir mes candidatures",
    "This job is no longer accepting applications.": "Cet emploi n'accepte plus de candidatures.",
    "Please log in to apply for this job.": "Veuillez vous connecter pour postuler à cet emploi.",
    "Log In": "Se connecter",
    "Back to Job Board": "Retour à la liste des emplois",
    "Manage Applications": "Gérer les candidatures",
    "views": "vues",
    "view": "vue",
    "applications": "candidatures",
    "application": "candidature",
    "By": "Par",
    "Edit Event": "Modifier l'événement",
    "Create Event": "Créer un événement",
    "Fill in the details below to create a new event": "Remplissez les détails ci-dessous pour créer un nouvel événement",
    "Basic Information": "Informations de base",
    "Date & Time": "Date et heure",
    "Provide a detailed description of the event": "Fournissez une description détaillée de l'événement",
    "Edit News Post": "Modifier l'article d'actualité",
    "Create News Post": "Créer un article d'actualité",
    "Create or edit a news announcement": "Créer ou modifier une annonce d'actualité",
    "Brief summary that will appear in lists (optional)": "Résumé bref qui apparaîtra dans les listes (optionnel)",
    "Folder": "Dossier",
    "Parent Folder": "Dossier parent",
    "Leave blank to create in root": "Laisser vide pour créer à la racine",
    "Default Access Level": "Niveau d'accès par défaut",
    "Default access level for documents in this folder": "Niveau d'accès par défaut pour les documents dans ce dossier",
    "URL-friendly identifier (e.g., folder-name)": "Identifiant convivial pour l'URL (ex. : nom-dossier)",
    "Slug": "Identifiant",
    "No recent activity to display.": "Aucune activité récente à afficher.",
    "View Details": "Voir les détails",
    "View Profile": "Voir le profil",
    "Main navigation": "Navigation principale",
    "Home": "Accueil",
    "Admin panel": "Panneau d'administration",
    "Members directory": "Répertoire des membres",
    "No applications yet": "Aucune candidature pour le moment",
    "Track the status of your job applications": "Suivez le statut de vos candidatures",
    "Applied": "Postulé",
    "Reviewed": "Examiné",
    "New Thread": "Nouveau fil",
    "Edit Thread": "Modifier le fil",
    "Create New Thread": "Créer un nouveau fil",
    "Tags (optional)": "Tags (optionnel)",
    "Add Your Reply": "Ajouter votre réponse",
    "Replies": "Réponses",
    "threads": "fils",
    "thread": "fil",
    "on waitlist": "sur liste d'attente",
    "spaces available": "places disponibles",
    "Full": "Complet",
    "Unlimited capacity": "Capacité illimitée",
    "downloads": "téléchargements",
    "download": "téléchargement",
    "registrations": "inscriptions",
    "registration": "inscription",
    "Warning:": "Attention :",
    "This tag is used by": "Ce tag est utilisé par",
    "document(s). You cannot delete it.": "document(s). Vous ne pouvez pas le supprimer.",
    "This category is used by": "Cette catégorie est utilisée par",
    "post(s). You cannot delete it.": "article(s). Vous ne pouvez pas le supprimer.",
    "event(s). You cannot delete it.": "événement(s). Vous ne pouvez pas le supprimer.",
    "Documents": "Documents",
    "Subfolders": "Sous-dossiers",
    "%(user)s mentioned you in a reply": "%(user)s vous a mentionné dans une réponse",
    "A new version will be automatically created.": "Une nouvelle version sera automatiquement créée.",
    "A new version will be created from the selected version. The current version will remain in history.": "Une nouvelle version sera créée à partir de la version sélectionnée. La version actuelle restera dans l'historique.",
    "Accepted formats: PDF, DOC, DOCX (max 10MB)": "Formats acceptés : PDF, DOC, DOCX (max 10MB)",
    "Access academic and career resources": "Accéder aux ressources académiques et professionnelles",
    "Activate selected bans": "Activer les bannissements sélectionnés",
    "Active Members": "Membres actifs",
    "Activity Overview": "Aperçu de l'activité",
    "Additional Details": "Détails supplémentaires",
    "Additional Information": "Informations supplémentaires",
}

# Extended Italian translations
ITALIAN_TRANSLATIONS = {
    "Dashboard": "Dashboard",
    "Admin": "Amministrazione",
    "Events": "Eventi",
    "News": "Notizie",
    "Forum": "Forum",
    "Documents": "Documenti",
    "Jobs": "Lavori",
    "Members": "Membri",
    "Messages": "Messaggi",
    "Profile": "Profilo",
    "Logout": "Disconnetti",
    "Login": "Accedi",
    "Register": "Registrati",
    "Save": "Salva",
    "Cancel": "Annulla",
    "Edit": "Modifica",
    "Delete": "Elimina",
    "Submit": "Invia",
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
    "ASCAI - Association of Cameroonian Students in Lazio": "ASCAI - Associazione degli Studenti Camerunensi nel Lazio",
    "ASCAI - Association of Cameroonian Students in Lazio, Italy": "ASCAI - Associazione degli Studenti Camerunensi nel Lazio, Italia",
    "Welcome to ASCAI": "Benvenuto in ASCAI",
    "Association of Cameroonian Students in Lazio, Italy": "Associazione degli Studenti Camerunensi nel Lazio, Italia",
    "Connecting Cameroonian students in the Lazio region, fostering community, and supporting academic excellence.": "Collegare gli studenti camerunensi nella regione del Lazio, favorire la comunità e sostenere l'eccellenza accademica.",
    "Join Us": "Unisciti a noi",
    "Go to Dashboard": "Vai alla Dashboard",
    "View News": "Vedi le notizie",
    "Account Activated": "Account attivato",
    "Your account has been successfully activated!": "Il tuo account è stato attivato con successo!",
    "Activate Account": "Attiva account",
    "Activate your ASCAI account": "Attiva il tuo account ASCAI",
    "Activation Link Invalid": "Link di attivazione non valido",
    "Please check your email and click the activation link to activate your account.": "Controlla la tua email e clicca sul link di attivazione per attivare il tuo account.",
    "Back to Login": "Torna al login",
    "Already have an account? Login here": "Hai già un account? Accedi qui",
    "Don't have an account? Register here": "Non hai un account? Registrati qui",
    "Change Password": "Cambia password",
    "Back to Profile": "Torna al profilo",
    "No events found.": "Nessun evento trovato.",
    "No news posts found.": "Nessun articolo trovato.",
    "No jobs found": "Nessun lavoro trovato",
    "Job Title": "Titolo del lavoro",
    "Company Name": "Nome azienda",
    "Location": "Posizione",
    "Job Type": "Tipo di lavoro",
    "Salary Range": "Fascia salariale",
    "From": "Da",
    "Up to": "Fino a",
    "Deadline": "Scadenza",
    "Application Deadline": "Scadenza candidatura",
    "Job Description": "Descrizione del lavoro",
    "Requirements": "Requisiti",
    "Posted by": "Pubblicato da",
    "Apply Now": "Candidati ora",
    "You have already applied to this job.": "Hai già fatto domanda per questo lavoro.",
    "View My Applications": "Vedi le mie candidature",
    "This job is no longer accepting applications.": "Questo lavoro non accetta più candidature.",
    "Please log in to apply for this job.": "Accedi per candidarti a questo lavoro.",
    "Log In": "Accedi",
    "Back to Job Board": "Torna alla lista lavori",
    "Manage Applications": "Gestisci candidature",
    "views": "visualizzazioni",
    "view": "visualizzazione",
    "applications": "candidature",
    "application": "candidatura",
    "By": "Da",
    "Edit Event": "Modifica evento",
    "Create Event": "Crea evento",
    "Fill in the details below to create a new event": "Compila i dettagli qui sotto per creare un nuovo evento",
    "Basic Information": "Informazioni di base",
    "Date & Time": "Data e ora",
    "Provide a detailed description of the event": "Fornisci una descrizione dettagliata dell'evento",
    "Edit News Post": "Modifica articolo",
    "Create News Post": "Crea articolo",
    "Create or edit a news announcement": "Crea o modifica un annuncio",
    "Brief summary that will appear in lists (optional)": "Breve riassunto che apparirà nelle liste (opzionale)",
    "Folder": "Cartella",
    "Parent Folder": "Cartella genitore",
    "Leave blank to create in root": "Lascia vuoto per creare nella root",
    "Default Access Level": "Livello di accesso predefinito",
    "Default access level for documents in this folder": "Livello di accesso predefinito per i documenti in questa cartella",
    "URL-friendly identifier (e.g., folder-name)": "Identificatore compatibile con URL (es. nome-cartella)",
    "Slug": "Identificatore",
    "No recent activity to display.": "Nessuna attività recente da visualizzare.",
    "View Details": "Vedi dettagli",
    "View Profile": "Vedi profilo",
    "Main navigation": "Navigazione principale",
    "Home": "Home",
    "Admin panel": "Pannello amministrazione",
    "Members directory": "Elenco membri",
    "No applications yet": "Nessuna candidatura ancora",
    "Track the status of your job applications": "Traccia lo stato delle tue candidature",
    "Applied": "Candidato",
    "Reviewed": "Revisionato",
    "New Thread": "Nuovo thread",
    "Edit Thread": "Modifica thread",
    "Create New Thread": "Crea nuovo thread",
    "Tags (optional)": "Tag (opzionale)",
    "Add Your Reply": "Aggiungi la tua risposta",
    "Replies": "Risposte",
    "threads": "thread",
    "thread": "thread",
    "on waitlist": "in lista d'attesa",
    "spaces available": "posti disponibili",
    "Full": "Pieno",
    "Unlimited capacity": "Capacità illimitata",
    "downloads": "download",
    "download": "download",
    "registrations": "iscrizioni",
    "registration": "iscrizione",
    "Warning:": "Attenzione:",
    "This tag is used by": "Questo tag è usato da",
    "document(s). You cannot delete it.": "documento(i). Non puoi eliminarlo.",
    "This category is used by": "Questa categoria è usata da",
    "post(s). You cannot delete it.": "articolo(i). Non puoi eliminarlo.",
    "event(s). You cannot delete it.": "evento(i). Non puoi eliminarlo.",
    "Documents": "Documenti",
    "Subfolders": "Sottocartelle",
    "%(user)s mentioned you in a reply": "%(user)s ti ha menzionato in una risposta",
    "A new version will be automatically created.": "Una nuova versione sarà creata automaticamente.",
    "A new version will be created from the selected version. The current version will remain in history.": "Una nuova versione sarà creata dalla versione selezionata. La versione corrente rimarrà nella cronologia.",
    "Accepted formats: PDF, DOC, DOCX (max 10MB)": "Formati accettati: PDF, DOC, DOCX (max 10MB)",
    "Access academic and career resources": "Accedi a risorse accademiche e professionali",
    "Activate selected bans": "Attiva ban selezionati",
    "Active Members": "Membri attivi",
    "Activity Overview": "Panoramica attività",
    "Additional Details": "Dettagli aggiuntivi",
    "Additional Information": "Informazioni aggiuntive",
}

def update_po_file_comprehensive(po_file_path, translations):
    """Update .po file with translations, handling multiline strings properly."""
    try:
        content = po_file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {po_file_path}: {e}")
        return False
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    updated_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for msgid line
        if line.strip().startswith('msgid '):
            msgid_line = line
            msgid_text = ""
            
            # Extract msgid (handle quoted strings)
            if '"' in msgid_line:
                # Single line msgid
                match = re.search(r'msgid\s+"([^"]*)"', msgid_line)
                if match:
                    msgid_text = match.group(1)
            else:
                # Might be multiline, skip for now
                new_lines.append(line)
                i += 1
                continue
            
            # Look for corresponding msgstr
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('msgstr '):
                msgstr_line = lines[i + 1]
                
                # Check if translation exists
                if msgid_text in translations:
                    translation = translations[msgid_text]
                    # Escape quotes
                    translation = translation.replace('\\', '\\\\').replace('"', '\\"')
                    new_lines.append(msgid_line)
                    new_lines.append(f'msgstr "{translation}"')
                    updated_count += 1
                    i += 2
                    continue
            
            new_lines.append(line)
        else:
            new_lines.append(line)
        
        i += 1
    
    if updated_count > 0:
        new_content = '\n'.join(new_lines)
        po_file_path.write_text(new_content, encoding='utf-8')
        print(f"Updated {po_file_path} with {updated_count} translations")
        return True
    
    return False

def main():
    """Update French and Italian .po files with comprehensive translations."""
    print("Adding comprehensive translations to .po files...")
    
    # Update French translations
    fr_po = BASE_DIR / "locale" / "fr" / "LC_MESSAGES" / "django.po"
    if fr_po.exists():
        update_po_file_comprehensive(fr_po, FRENCH_TRANSLATIONS)
    else:
        print(f"French .po file not found: {fr_po}")
    
    # Update Italian translations
    it_po = BASE_DIR / "locale" / "it" / "LC_MESSAGES" / "django.po"
    if it_po.exists():
        update_po_file_comprehensive(it_po, ITALIAN_TRANSLATIONS)
    else:
        print(f"Italian .po file not found: {it_po}")
    
    print("\nDone! Now run compile_translations.py to compile .mo files")

if __name__ == "__main__":
    main()

