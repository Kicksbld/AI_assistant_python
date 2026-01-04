# =========================
# Booking Skill
# =========================

from typing import Dict
from agent import Skill, Slot


def booking_on_ready(values: Dict[str, str]) -> str:
    restaurant = values.get("restaurant_name", "un restaurant")
    date = values.get("date", "une date inconnue")
    time = values.get("time", "une heure inconnue")
    people = values.get("people", "un certain nombre de")

    return (
        f"Parfait ! Je récapitule : réservation à {restaurant}, "
        f"le {date} à {time}, pour {people} personnes. "
        f"(Je ne fais pas la réservation réelle, c'est un exemple.)"
    )


def create_booking_skill() -> Skill:
    """Crée et retourne le skill réservation de restaurant"""
    booking_slots = [
        Slot(
            name="restaurant_name",
            description="le nom du restaurant ou type de cuisine (ex: italien, japonais)",
            question="Dans quel restaurant ou quel type de cuisine veux-tu réserver ?",
        ),
        Slot(
            name="date",
            description="la date de la réservation",
            question="Pour quel jour veux-tu réserver ?",
        ),
        Slot(
            name="time",
            description="l'heure de la réservation",
            question="À quelle heure ?",
        ),
        Slot(
            name="people",
            description="le nombre de personnes",
            question="Pour combien de personnes ?",
        ),
    ]

    return Skill(
        name="booking",
        description="organisation d'une réservation de restaurant",
        slots=booking_slots,
        final_answer_system_prompt="""
Tu es un assistant qui aide à réserver un restaurant.
Tu reçois soit des données structurées, soit un résumé, et tu dois
répondre en français en récapitulant clairement la réservation.
""",
        on_ready=booking_on_ready,
    )
