# =========================
# Calendar Skill
# =========================

from typing import Any, Dict, List
import os
from agent import Skill, Slot
import json


CALENDAR_FILE = "./Files/calendar.json"


def load_calendar() -> List[Dict[str, Any]]:
    """Charge le calendrier (liste d'événements)"""
    if not os.path.exists(CALENDAR_FILE):
        return []
    try:
        with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_calendar(events: List[Dict[str, Any]]) -> None:
    """Sauvegarde les événements dans calendar.json"""
    os.makedirs("./Files", exist_ok=True)
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def calendar_on_ready(values: Dict[str, str]) -> Dict[str, Any]:
    action = values.get("action")

    # Load events
    events = load_calendar()

    # -------------------------
    # ACTION : ADD EVENT
    # -------------------------
    if action == "add":
        title = values.get("title")
        date = values.get("date")

        new_event = {
            "id": f"evt_{len(events)+1}",
            "title": title,
            "date": date
        }

        events.append(new_event)
        save_calendar(events)

        return {
            "type": "calendar_success",
            "action": "add",
            "event": new_event,
            "message": f"L'événement '{title}' du {date} a été ajouté."
        }

    # -------------------------
    # ACTION : REMOVE EVENT
    # -------------------------
    if action == "remove":
        event_id = values.get("event_id")
        new_list = [e for e in events if e["id"] != event_id]

        if len(new_list) == len(events):
            return {
                "type": "calendar_error",
                "message": f"Aucun événement trouvé avec l'id '{event_id}'."
            }

        save_calendar(new_list)
        return {
            "type": "calendar_success",
            "action": "remove",
            "event_id": event_id,
            "message": f"L'événement avec l'id '{event_id}' a été supprimé."
        }

    # -------------------------
    # ACTION : EDIT EVENT
    # -------------------------
    if action == "edit":
        event_id = values.get("event_id")
        new_title = values.get("new_title")
        new_date = values.get("new_date")

        found = False
        for e in events:
            if e["id"] == event_id:
                if new_title:
                    e["title"] = new_title
                if new_date:
                    e["date"] = new_date
                found = True

        if not found:
            return {
                "type": "calendar_error",
                "message": f"Aucun événement trouvé avec l'id '{event_id}'."
            }

        save_calendar(events)
        return {
            "type": "calendar_success",
            "action": "edit",
            "event_id": event_id,
            "message": f"L'événement '{event_id}' a été mis à jour."
        }

    # -------------------------
    # ACTION : LIST EVENTS
    # -------------------------
    if action == "list":
        return {
            "type": "calendar_success",
            "action": "list",
            "events": events,
            "message": f"Voici la liste de tes événements ({len(events)} total)."
        }

    # -------------------------
    # ACTION INCONNUE
    # -------------------------
    return {
        "type": "calendar_error",
        "message": "Action inconnue. Utilise : add, remove, edit, list."
    }


def create_calendar_skill() -> Skill:
    """Crée et retourne le skill calendar"""

    calendar_slots = [
        Slot(
            name="action",
            description="L'action voulue : add, remove, edit, list",
            question="Que veux-tu faire ? (add/remove/edit/list)"
        ),
        Slot(
            name="title",
            description="[add] Le titre de l'événement",
            question="Quel est le titre de l'événement ?",
            depends_on={"action": "add"},
        ),
        Slot(
            name="date",
            description="[add] La date de l'événement",
            question="À quelle date ?",
            depends_on={"action": "add"},
        ),
        Slot(
            name="event_id",
            description="[remove/edit] L'identifiant de l'événement",
            question="Quel est l'id de l'événement ?",
            depends_on={"action": ["remove", "edit"]},
        ),
        Slot(
            name="new_title",
            description="[edit] Nouveau titre (optionnel)",
            question="Quel nouveau titre veux-tu donner ? (ou laisse vide)",
            depends_on={"action": "edit"},
            required=False
        ),
        Slot(
            name="new_date",
            description="[edit] Nouvelle date (optionnel)",
            question="Quelle est la nouvelle date ? (ou laisse vide)",
            depends_on={"action": "edit"},
            required=False
        ),
    ]

    return Skill(
        name="calendar",
        description="Gestion simple d'un calendrier avec ajout, suppression, édition ou listing d'événements.",
        slots=calendar_slots,
        final_answer_system_prompt="""
Tu es un assistant qui gère un calendrier simple.
Tu reçois des données structurées avec une action et les informations d'un événement.
Si c'est un succès, informe clairement l'utilisateur du résultat.
Si c'est une erreur, explique le problème simplement.
Réponds en français, de manière naturelle et concise.
""",
        on_ready=calendar_on_ready,
    )