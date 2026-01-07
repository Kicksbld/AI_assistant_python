# =========================
# Email Skill - Simulated Emails
# =========================

from typing import Any, Dict, List, Optional
import os
import json
from agent import Skill, Slot, send_llama_chat

# Constants
EMAIL_FILE = "./Files/emails.json"


# =========================
# Helper Functions
# =========================

def load_emails() -> List[Dict]:
    """
    Charge les emails depuis le fichier JSON.
    Retourne une liste vide si le fichier n'existe pas.
    """
    if not os.path.exists(EMAIL_FILE):
        return []

    try:
        with open(EMAIL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('emails', [])
    except Exception as e:
        print(f"Erreur lors du chargement des emails: {e}")
        return []


def save_emails(emails: List[Dict]) -> None:
    """
    Sauvegarde les emails au format JSON.
    Crée le dossier Files si nécessaire.
    """
    os.makedirs("./Files", exist_ok=True)
    try:
        with open(EMAIL_FILE, 'w', encoding='utf-8') as f:
            json.dump({"emails": emails}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des emails: {e}")


def find_email_by_id(emails: List[Dict], email_id: str) -> Optional[Dict]:
    """
    Recherche un email par son ID.
    Supporte à la fois les IDs complets ('email_001') et les raccourcis numériques ('1').
    """
    # Essayer d'abord une correspondance exacte
    for email in emails:
        if email.get('id') == email_id:
            return email

    # Essayer le raccourci numérique (ex: '1' -> 'email_001')
    if email_id.isdigit():
        padded_id = f"email_{email_id.zfill(3)}"
        for email in emails:
            if email.get('id') == padded_id:
                return email

    return None


def synthesize_email_with_llm(email_body: str) -> str:
    """
    Utilise le LLaMA local pour générer un résumé concis de l'email.
    """
    system_prompt = """Tu es un assistant qui résume les emails de manière concise.
Tu dois extraire l'information principale et la présenter de façon claire en 2-3 phrases maximum.
Réponds en français de manière naturelle et concise."""

    try:
        synthesis = send_llama_chat(
            system_prompt=system_prompt,
            user_content=f"Résume cet email:\n\n{email_body}",
            temperature=0.7,
            max_tokens=256,
        )
        return synthesis
    except Exception as e:
        return f"Erreur lors de la synthèse: {str(e)}"


def initialize_sample_emails() -> List[Dict]:
    """
    Crée 8 emails d'exemple réalistes en français.
    Couvre différents scénarios: université, personnel, notifications.
    """
    return [
        {
            "id": "email_001",
            "from": "prof.martin@university.fr",
            "from_name": "Prof. Martin",
            "subject": "Rappel rendu TP Agent Conversationnel",
            "date": "2026-01-07 09:30",
            "body": "Bonjour,\n\nJe vous rappelle que le rendu du TP sur les agents conversationnels est prévu pour vendredi 10 janvier à 23h59. N'oubliez pas d'inclure:\n- Le code source complet\n- Un fichier README avec les instructions d'installation\n- Un rapport de 2-3 pages expliquant votre architecture\n\nSi vous avez des questions, n'hésitez pas.\n\nCordialement,\nProf. Martin",
            "read": False
        },
        {
            "id": "email_002",
            "from": "scolarite@university.fr",
            "from_name": "Service Scolarité",
            "subject": "Planning des examens - Session janvier 2026",
            "date": "2026-01-06 14:20",
            "body": "Chers étudiants,\n\nVoici le planning des examens pour la session de janvier 2026:\n\n- 15/01: Intelligence Artificielle (9h-12h, Amphi A)\n- 17/01: Bases de données avancées (14h-17h, Amphi B)\n- 20/01: Systèmes distribués (9h-12h, Amphi A)\n\nMerci de vous présenter 15 minutes avant le début de l'épreuve avec votre carte d'étudiant.\n\nBonne chance à tous!",
            "read": False
        },
        {
            "id": "email_003",
            "from": "marie.dupont@gmail.com",
            "from_name": "Marie",
            "subject": "Re: Weekend prochain ?",
            "date": "2026-01-05 18:45",
            "body": "Salut !\n\nOui super idée pour samedi ! Je propose qu'on se retrouve vers 14h au parc pour faire un foot, et après on peut aller manger quelque chose en ville.\n\nTu peux demander à Thomas et Lucas s'ils sont dispos ?\n\nÀ samedi !\nMarie",
            "read": True
        },
        {
            "id": "email_004",
            "from": "newsletter@techcrunch.com",
            "from_name": "TechCrunch",
            "subject": "🚀 Les actus tech de la semaine",
            "date": "2026-01-05 08:00",
            "body": "Votre résumé tech hebdomadaire:\n\n📱 Apple annonce de nouvelles fonctionnalités IA pour Siri\n🤖 OpenAI lance GPT-5 avec des capacités de raisonnement améliorées\n💻 Google dévoile sa nouvelle puce Tensor G5\n🔋 Tesla bat des records de production au Q4 2025\n\nCliquez pour lire les articles complets...",
            "read": False
        },
        {
            "id": "email_005",
            "from": "security@amazon.fr",
            "from_name": "Amazon Sécurité",
            "subject": "Activité inhabituelle détectée sur votre compte",
            "date": "2026-01-04 22:15",
            "body": "Bonjour,\n\nNous avons détecté une tentative de connexion à votre compte Amazon depuis un nouvel appareil (iPhone, Paris).\n\nSi c'était vous, aucune action n'est nécessaire. Sinon, nous vous recommandons de:\n1. Changer immédiatement votre mot de passe\n2. Activer la vérification en deux étapes\n\nPour sécuriser votre compte, cliquez ici.\n\nL'équipe Amazon",
            "read": True
        },
        {
            "id": "email_006",
            "from": "papa@gmail.com",
            "from_name": "Papa",
            "subject": "Anniversaire de Mamie - 25 janvier",
            "date": "2026-01-03 19:30",
            "body": "Salut,\n\nPetit rappel que l'anniversaire de Mamie est le 25 janvier. On organise une fête surprise chez elle à 15h.\n\nEst-ce que tu peux venir ? Et si oui, tu peux apporter le gâteau ? Mamie adore les fraisiers.\n\nTiens-moi au courant avant le 15 pour qu'on organise.\n\nBises,\nPapa",
            "read": False
        },
        {
            "id": "email_007",
            "from": "thomas.bernard@university.fr",
            "from_name": "Thomas Bernard",
            "subject": "Projet IA - Réunion mercredi ?",
            "date": "2026-01-02 16:20",
            "body": "Salut,\n\nJ'ai avancé sur la partie classification du projet d'IA. J'ai réussi à obtenir 94% de précision avec un ResNet50 pré-entraîné.\n\nOn peut se voir mercredi après-midi pour faire le point ? Je pense qu'on peut commencer à rédiger le rapport si la partie NLP est aussi terminée de ton côté.\n\nDis-moi si 14h te va ?\n\nThomas",
            "read": False
        },
        {
            "id": "email_008",
            "from": "noreply@laposte.fr",
            "from_name": "La Poste",
            "subject": "Votre colis arrive demain",
            "date": "2026-01-02 11:45",
            "body": "Bonjour,\n\nVotre colis n° 6Z89475329 sera livré demain (3 janvier) entre 9h et 13h.\n\nVous pouvez suivre votre livraison en temps réel via notre application mobile.\n\nSi vous êtes absent, le colis sera déposé en point relais.\n\nCordialement,\nLa Poste",
            "read": True
        }
    ]


# =========================
# Operation Handlers
# =========================

def handle_list_emails(emails: List[Dict]) -> Dict[str, Any]:
    """
    Liste tous les emails avec prévisualisation.
    Trie par date (plus récent en premier).
    """
    try:
        # Trier par date (plus récent en premier)
        sorted_emails = sorted(emails, key=lambda e: e.get('date', ''), reverse=True)

        # Créer la liste avec prévisualisation
        email_list = []
        unread_count = 0

        for email in sorted_emails:
            if not email.get('read', False):
                unread_count += 1

            # Prévisualisation: premiers 80 caractères
            body = email.get('body', '')
            preview = body[:80] + "..." if len(body) > 80 else body
            preview = preview.replace('\n', ' ')

            email_list.append({
                'id': email['id'],
                'from_name': email.get('from_name', email.get('from', '')),
                'subject': email.get('subject', 'Sans objet'),
                'date': email.get('date', ''),
                'preview': preview,
                'read': email.get('read', False)
            })

        return {
            "type": "email_success",
            "action": "list",
            "emails": email_list,
            "count": len(emails),
            "unread_count": unread_count,
            "message": f"Voici tes {len(emails)} emails ({unread_count} non lus) :"
        }

    except Exception as e:
        return {
            "type": "email_error",
            "message": f"Erreur lors du listing : {str(e)}"
        }


def handle_read_email(emails: List[Dict], email_id: str) -> Dict[str, Any]:
    """
    Lit un email spécifique et le marque comme lu.
    """
    try:
        email = find_email_by_id(emails, email_id)

        if not email:
            return {
                "type": "email_error",
                "message": f"Aucun email trouvé avec l'ID '{email_id}'."
            }

        # Marquer comme lu et sauvegarder
        email['read'] = True
        save_emails(emails)

        return {
            "type": "email_success",
            "action": "read",
            "email": {
                'id': email['id'],
                'from': email.get('from', ''),
                'from_name': email.get('from_name', ''),
                'subject': email.get('subject', 'Sans objet'),
                'date': email.get('date', ''),
                'body': email.get('body', ''),
                'read': True
            },
            "message": f"Voici le contenu du mail de {email.get('from_name', 'Expéditeur')} :"
        }

    except Exception as e:
        return {
            "type": "email_error",
            "message": f"Erreur lors de la lecture : {str(e)}"
        }


def handle_synthesize_email(emails: List[Dict], email_info: str) -> Dict[str, Any]:
    """
    Synthétise un ou plusieurs emails en utilisant le LLM local.
    Supporte la synthèse d'un email spécifique ou de tous les emails non lus.
    """
    try:
        # Déterminer quels emails synthétiser
        emails_to_synthesize = []

        if email_info.lower() in ['tous', 'all', 'toutes', '']:
            # Synthétiser tous les emails non lus
            emails_to_synthesize = [e for e in emails if not e.get('read', False)]
            if not emails_to_synthesize:
                return {
                    "type": "email_error",
                    "message": "Aucun email non lu à synthétiser."
                }
        else:
            # Synthétiser un email spécifique
            email = find_email_by_id(emails, email_info)
            if not email:
                return {
                    "type": "email_error",
                    "message": f"Aucun email trouvé avec l'ID '{email_info}'."
                }
            emails_to_synthesize = [email]

        # Générer les synthèses avec le LLM
        syntheses = []
        for email in emails_to_synthesize:
            summary = synthesize_email_with_llm(email.get('body', ''))

            syntheses.append({
                'id': email['id'],
                'from_name': email.get('from_name', ''),
                'subject': email.get('subject', ''),
                'date': email.get('date', ''),
                'summary': summary
            })

            # Marquer comme lu
            email['read'] = True

        # Sauvegarder le statut mis à jour
        save_emails(emails)

        return {
            "type": "email_success",
            "action": "synthesize",
            "syntheses": syntheses,
            "count": len(syntheses),
            "message": f"Voici la synthèse de {len(syntheses)} email(s) :"
        }

    except Exception as e:
        return {
            "type": "email_error",
            "message": f"Erreur lors de la synthèse : {str(e)}"
        }


# =========================
# Main Handler
# =========================

def email_on_ready(values: Dict[str, str]) -> Dict[str, Any]:
    """
    Handler principal du skill email.
    Route vers les handlers spécifiques selon l'action.
    """
    action = values.get("action", "").lower()
    email_info = values.get("email_info", "")

    # Charger les emails
    emails = load_emails()

    # Initialiser avec des emails d'exemple si le fichier n'existe pas
    if not emails:
        emails = initialize_sample_emails()
        save_emails(emails)

    # Router vers l'opération appropriée
    if action in ["list", "lister", "voir", "afficher", "show"]:
        return handle_list_emails(emails)
    elif action in ["read", "lire", "ouvrir", "open"]:
        return handle_read_email(emails, email_info)
    elif action in ["synthesize", "synthétiser", "synthetiser", "résumer", "resumer", "summary"]:
        return handle_synthesize_email(emails, email_info)
    else:
        return {
            "type": "email_error",
            "message": f"Action non reconnue: '{action}'. Utilise: list, read, ou synthesize."
        }


# =========================
# Skill Definition
# =========================

def create_email_skill() -> Skill:
    """Crée et retourne le skill email"""
    email_slots = [
        Slot(
            name="action",
            description=(
                "L'action voulue: "
                "list (lister les emails), "
                "read (lire un email spécifique), "
                "synthesize (synthétiser/résumer un ou plusieurs emails)"
            ),
            question="Que veux-tu faire avec tes emails ? (lister/lire/synthétiser)"
        ),
        Slot(
            name="email_info",
            description=(
                "L'ID ou le numéro de l'email pour les actions read et synthesize. "
                "Pour LIST: laisser vide. "
                "Pour READ: ID de l'email (ex: 'email_001' ou '1'). "
                "Pour SYNTHESIZE: ID de l'email, ou 'tous'/'all' pour synthétiser tous les emails non lus."
            ),
            question="Quel email veux-tu consulter ? (donne l'ID, ou dis 'tous' pour synthétiser tout)"
        )
    ]

    return Skill(
        name="email",
        description=(
            "Consultation, lecture et synthèse d'emails. "
            "Utilise cette skill quand l'utilisateur demande de lire, lister ou résumer ses emails"
        ),
        slots=email_slots,
        final_answer_system_prompt="""
Tu es un assistant qui aide à consulter et synthétiser les emails.
Tu reçois des données structurées avec les emails et leurs synthèses.
Si c'est un succès, présente les informations de manière claire et engageante.
Pour les listes d'emails, montre les plus importants (non lus) en premier.
Pour les synthèses, présente-les de manière concise et structurée.
Si c'est une erreur, explique le problème simplement.
Réponds en français de façon naturelle et concise.
""",
        on_ready=email_on_ready
    )
