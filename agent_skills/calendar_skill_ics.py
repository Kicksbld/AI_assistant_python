# =========================
# Calendar Skill - ICS Format
# =========================

from typing import Any, Dict, List, Optional
import os
import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from dateutil import parser as dateutil_parser
import pytz
import random

from agent import Skill, Slot

# Constants
CALENDAR_FILE = "./Files/calendar.ics"
PARIS_TZ = pytz.timezone('Europe/Paris')


# =========================
# Helper Functions
# =========================

def load_calendar() -> Calendar:
    """
    Charge le calendrier ICS depuis le fichier.
    Retourne un calendrier vide si le fichier n'existe pas.
    """
    if not os.path.exists(CALENDAR_FILE):
        # Créer un nouveau calendrier avec les propriétés requises
        cal = Calendar()
        cal.add('prodid', '-//Home Assistant Agent//FR')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        return cal

    try:
        with open(CALENDAR_FILE, 'rb') as f:
            return Calendar.from_ical(f.read())
    except Exception as e:
        print(f"Erreur lors du chargement du calendrier: {e}")
        # Retourner un calendrier vide en cas d'erreur
        cal = Calendar()
        cal.add('prodid', '-//Home Assistant Agent//FR')
        cal.add('version', '2.0')
        return cal


def save_calendar(cal: Calendar) -> None:
    """
    Sauvegarde le calendrier au format ICS.
    Crée le dossier Files si nécessaire.
    """
    os.makedirs("./Files", exist_ok=True)
    try:
        with open(CALENDAR_FILE, 'wb') as f:
            f.write(cal.to_ical())
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du calendrier: {e}")


def find_event_by_uid(cal: Calendar, uid: str) -> Optional[Event]:
    """
    Recherche un événement par son UID dans le calendrier.
    Retourne l'événement ou None s'il n'est pas trouvé.
    """
    for component in cal.walk():
        if component.name == "VEVENT":
            if str(component.get('uid', '')) == uid:
                return component
    return None


def generate_event_uid() -> str:
    """
    Génère un UID unique pour un nouvel événement.
    Format: evt_<timestamp>_<random>@homeassistant.local
    """
    timestamp = int(datetime.now().timestamp())
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    return f"evt_{timestamp}_{random_suffix}@homeassistant.local"


def parse_french_datetime(date_str: str, time_str: str = None) -> datetime:
    """
    Parse les dates et heures en français naturel.

    Exemples:
      - "aujourd'hui" -> aujourd'hui à midi
      - "demain" -> demain à midi
      - "14h30" -> 14:30
      - "2026-01-15" -> date parsée

    Retourne un datetime en timezone Europe/Paris.
    """
    if not date_str:
        date_str = "aujourd'hui"

    # Normaliser
    date_lower = date_str.lower().strip()

    # Pattern matching pour les dates françaises
    today = datetime.now(PARIS_TZ)

    if date_lower in ["aujourd'hui", "aujourdhui", "today", "auj"]:
        base_date = today
    elif date_lower in ["demain", "tomorrow", "tmr"]:
        base_date = today + timedelta(days=1)
    elif date_lower in ["après-demain", "apres-demain", "après demain", "apres demain"]:
        base_date = today + timedelta(days=2)
    elif match := re.match(r'dans (\d+) jours?', date_lower):
        days = int(match.group(1))
        base_date = today + timedelta(days=days)
    else:
        # Essayer de parser avec dateutil
        try:
            parsed_date = dateutil_parser.parse(date_str, dayfirst=True)
            if parsed_date.tzinfo is None:
                base_date = PARIS_TZ.localize(parsed_date)
            else:
                base_date = parsed_date.astimezone(PARIS_TZ)
        except:
            # Par défaut: aujourd'hui
            base_date = today

    # Parser l'heure si fournie
    if time_str:
        time_lower = time_str.lower().strip()
        hour, minute = 12, 0  # Défaut

        # Patterns: "14h30", "14:30", "14h", "2pm", etc.
        if match := re.match(r'(\d{1,2})[h:](\d{2})', time_lower):
            hour, minute = int(match.group(1)), int(match.group(2))
        elif match := re.match(r'(\d{1,2})h', time_lower):
            hour = int(match.group(1))
            minute = 0
        else:
            try:
                parsed_time = dateutil_parser.parse(time_str)
                hour, minute = parsed_time.hour, parsed_time.minute
            except:
                pass

        return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Pas d'heure fournie: midi par défaut
    return base_date.replace(hour=12, minute=0, second=0, microsecond=0)


def parse_duration(duration_str: str) -> timedelta:
    """
    Parse une durée en français.

    Exemples:
      - "1h", "1 heure" -> 1 heure
      - "30min", "30 minutes" -> 30 minutes
      - "2h30" -> 2h30

    Retourne un timedelta.
    """
    if not duration_str:
        return timedelta(hours=1)  # Durée par défaut: 1 heure

    duration_lower = duration_str.lower().strip()

    # Pattern: "2h30", "2h30min"
    if match := re.match(r'(\d+)h(\d+)', duration_lower):
        hours = int(match.group(1))
        minutes = int(match.group(2))
        return timedelta(hours=hours, minutes=minutes)

    # Pattern: "2h", "2 heures"
    if match := re.match(r'(\d+)\s*h(?:eures?)?', duration_lower):
        hours = int(match.group(1))
        return timedelta(hours=hours)

    # Pattern: "30min", "30 minutes"
    if match := re.match(r'(\d+)\s*min(?:utes?)?', duration_lower):
        minutes = int(match.group(1))
        return timedelta(minutes=minutes)

    # Par défaut: 1 heure
    return timedelta(hours=1)


def list_events_summary(cal: Calendar) -> List[Dict[str, str]]:
    """
    Extrait un résumé de tous les événements du calendrier.
    Retourne une liste de dictionnaires avec les infos principales.
    """
    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            uid = str(component.get('uid', ''))
            summary = str(component.get('summary', 'Sans titre'))
            dtstart = component.get('dtstart')
            dtend = component.get('dtend')
            description = str(component.get('description', ''))

            # Formater les dates
            if dtstart:
                if hasattr(dtstart.dt, 'strftime'):
                    date_str = dtstart.dt.strftime('%Y-%m-%d')
                    time_str = dtstart.dt.strftime('%H:%M') if hasattr(dtstart.dt, 'hour') else ''
                else:
                    date_str = str(dtstart.dt)
                    time_str = ''
            else:
                date_str = ''
                time_str = ''

            events.append({
                'uid': uid,
                'summary': summary,
                'date': date_str,
                'time': time_str,
                'description': description
            })

    # Trier par date
    events.sort(key=lambda e: e['date'])
    return events


# =========================
# Operation Handlers
# =========================

def handle_add_event(cal: Calendar, info: str) -> Dict[str, Any]:
    """
    Ajoute un nouvel événement au calendrier.

    Info attendu: titre, date, heure, description, durée (séparés ou en langage naturel)
    """
    try:
        # Parser l'info avec des patterns simples
        # Format attendu: "titre | date | heure | description | durée"
        # Ou langage naturel que l'on essaie de parser

        # Valeurs par défaut
        title = "Sans titre"
        date_str = "aujourd'hui"
        time_str = "12h"
        description = ""
        duration_str = "1h"

        # Essayer de décomposer l'info
        if '|' in info:
            parts = [p.strip() for p in info.split('|')]
            if len(parts) >= 1:
                title = parts[0]
            if len(parts) >= 2:
                date_str = parts[1]
            if len(parts) >= 3:
                time_str = parts[2]
            if len(parts) >= 4:
                description = parts[3]
            if len(parts) >= 5:
                duration_str = parts[4]
        else:
            # Tentative de parsing simple
            # Chercher un titre (début jusqu'à un mot-clé de date)
            date_keywords = ['demain', 'aujourd', 'dans', 'le ', 'à ', '2026', '2025']
            found_keyword = False
            for keyword in date_keywords:
                if keyword in info.lower():
                    idx = info.lower().index(keyword)
                    title = info[:idx].strip()
                    rest = info[idx:].strip()
                    # Le reste contient date/heure/description
                    # On fait simple: tout est dans rest
                    date_str = rest
                    found_keyword = True
                    break

            if not found_keyword:
                title = info  # Tout est le titre

        # Parser date et heure
        dtstart = parse_french_datetime(date_str, time_str)
        duration = parse_duration(duration_str)
        dtend = dtstart + duration

        # Créer l'événement
        event = Event()
        event.add('uid', generate_event_uid())
        event.add('summary', title)
        event.add('dtstart', dtstart)
        event.add('dtend', dtend)
        if description:
            event.add('description', description)
        event.add('dtstamp', datetime.now(PARIS_TZ))

        # Ajouter au calendrier
        cal.add_component(event)
        save_calendar(cal)

        return {
            "type": "calendar_success",
            "action": "add",
            "event": {
                "uid": str(event.get('uid')),
                "summary": title,
                "dtstart": dtstart.strftime('%Y-%m-%d %H:%M'),
                "dtend": dtend.strftime('%Y-%m-%d %H:%M'),
                "description": description
            },
            "message": f"L'événement '{title}' a été ajouté pour le {dtstart.strftime('%d/%m/%Y à %H:%M')}."
        }

    except Exception as e:
        return {
            "type": "calendar_error",
            "message": f"Erreur lors de l'ajout de l'événement : {str(e)}"
        }


def handle_remove_event(cal: Calendar, uid: str) -> Dict[str, Any]:
    """
    Supprime un événement du calendrier par son UID.
    """
    try:
        event = find_event_by_uid(cal, uid)

        if not event:
            return {
                "type": "calendar_error",
                "message": f"Aucun événement trouvé avec l'UID '{uid}'."
            }

        # Récupérer le titre avant suppression
        summary = str(event.get('summary', 'Sans titre'))

        # Supprimer l'événement
        cal.subcomponents = [comp for comp in cal.subcomponents if comp.get('uid') != uid]
        save_calendar(cal)

        return {
            "type": "calendar_success",
            "action": "remove",
            "event_uid": uid,
            "message": f"L'événement '{summary}' (UID: {uid}) a été supprimé."
        }

    except Exception as e:
        return {
            "type": "calendar_error",
            "message": f"Erreur lors de la suppression : {str(e)}"
        }


def handle_edit_event(cal: Calendar, info: str) -> Dict[str, Any]:
    """
    Modifie un événement existant.

    Info attendu: "UID | nouveau_titre | nouvelle_date | nouvelle_heure | nouvelle_description"
    Les champs vides ne sont pas modifiés.
    """
    try:
        # Parser l'info
        parts = [p.strip() for p in info.split('|')]

        if len(parts) < 1:
            return {
                "type": "calendar_error",
                "message": "UID manquant pour la modification."
            }

        uid = parts[0]
        event = find_event_by_uid(cal, uid)

        if not event:
            return {
                "type": "calendar_error",
                "message": f"Aucun événement trouvé avec l'UID '{uid}'."
            }

        # Modifier les champs fournis
        if len(parts) >= 2 and parts[1]:
            event['summary'] = parts[1]

        if len(parts) >= 3 and parts[2]:
            # Nouvelle date
            new_time_str = parts[3] if len(parts) >= 4 and parts[3] else None
            new_dtstart = parse_french_datetime(parts[2], new_time_str)

            # Conserver la durée originale
            old_dtstart = event.get('dtstart').dt
            old_dtend = event.get('dtend').dt
            if hasattr(old_dtstart, 'hour') and hasattr(old_dtend, 'hour'):
                duration = old_dtend - old_dtstart
            else:
                duration = timedelta(hours=1)

            event['dtstart'] = new_dtstart
            event['dtend'] = new_dtstart + duration

        if len(parts) >= 5 and parts[4]:
            event['description'] = parts[4]

        # Mettre à jour last-modified
        event['last-modified'] = datetime.now(PARIS_TZ)

        save_calendar(cal)

        return {
            "type": "calendar_success",
            "action": "edit",
            "event_uid": uid,
            "message": f"L'événement '{event.get('summary')}' a été modifié."
        }

    except Exception as e:
        return {
            "type": "calendar_error",
            "message": f"Erreur lors de la modification : {str(e)}"
        }


def handle_list_events(cal: Calendar) -> Dict[str, Any]:
    """
    Liste tous les événements du calendrier.
    """
    try:
        events = list_events_summary(cal)

        return {
            "type": "calendar_success",
            "action": "list",
            "events": events,
            "count": len(events),
            "message": f"Voici tes {len(events)} événement(s) :"
        }

    except Exception as e:
        return {
            "type": "calendar_error",
            "message": f"Erreur lors du listing : {str(e)}"
        }


# =========================
# Main Handler
# =========================

def calendar_on_ready(values: Dict[str, str]) -> Dict[str, Any]:
    """
    Handler principal du skill calendrier.
    Route vers les handlers spécifiques selon l'action.
    """
    action = values.get("action", "").lower()
    event_info = values.get("event_info", "")

    # Charger le calendrier
    cal = load_calendar()

    # Router vers l'opération appropriée
    if action in ["add", "ajouter", "creer", "créer", "nouveau"]:
        return handle_add_event(cal, event_info)
    elif action in ["remove", "supprimer", "delete", "effacer"]:
        return handle_remove_event(cal, event_info)
    elif action in ["edit", "modifier", "update", "changer"]:
        return handle_edit_event(cal, event_info)
    elif action in ["list", "lister", "voir", "afficher", "show"]:
        return handle_list_events(cal)
    else:
        return {
            "type": "calendar_error",
            "message": f"Action non reconnue : '{action}'. Utilise : add, remove, edit, ou list."
        }


# =========================
# Skill Definition
# =========================

def create_calendar_skill() -> Skill:
    """Crée et retourne le skill calendrier ICS"""
    calendar_slots = [
        Slot(
            name="action",
            description="L'action voulue : add (ajouter), remove (supprimer), edit (modifier), list (lister)",
            question="Que veux-tu faire avec le calendrier ? (ajouter/supprimer/modifier/lister)"
        ),
        Slot(
            name="event_info",
            description=(
                "Les détails de l'événement selon l'action. "
                "Pour ADD: titre | date | heure | description | durée. "
                "Pour REMOVE: l'UID de l'événement à supprimer. "
                "Pour EDIT: UID | nouveau_titre | nouvelle_date | nouvelle_heure | nouvelle_description. "
                "Pour LIST: laisser vide ou dire 'tous'."
            ),
            question="Donne-moi les détails nécessaires pour cette action."
        )
    ]

    return Skill(
        name="calendar",
        description="Gestion d'un calendrier avec ajout, suppression, modification et listing d'événements",
        slots=calendar_slots,
        final_answer_system_prompt="""
Tu es un assistant qui gère un calendrier simple.
Tu reçois des données structurées avec une action et les informations d'un événement.
Si c'est un succès, informe clairement l'utilisateur du résultat.
Si c'est une erreur, explique le problème simplement.
Réponds en français, de manière naturelle et concise.
""",
        on_ready=calendar_on_ready
    )
