# =========================
# Weather Skill
# =========================

from typing import Any, Dict
from agent import Skill, Slot


def weather_on_ready(values: Dict[str, str]) -> Dict[str, Any]:
    city = values.get("city")
    date = values.get("date")

    return {
        "type": "weather_result",
        "city": city,
        "date": date,
        "forecast": {
            "summary": "ensoleillé avec quelques nuages",
            "temperature_min": 5,
            "temperature_max": 14,
        },
        "note": "Les données météo sont fictives dans cet exemple.",
    }


def create_weather_skill() -> Skill:
    """Crée et retourne le skill météo"""
    weather_slots = [
        Slot(
            name="city",
            description="la ville pour la météo (ex: Annecy, Paris, Lyon)",
            question="Pour quelle ville veux-tu la météo ?",
        ),
        Slot(
            name="date",
            description="la date pour la météo (ex: aujourd'hui, demain, 2025-12-15)",
            question="Pour quelle date veux-tu la météo ?",
        ),
    ]

    return Skill(
        name="weather",
        description="questions à propos de la météo en fonction d'une ville et d'une date",
        slots=weather_slots,
        final_answer_system_prompt="""
Tu es un assistant météo.
Tu reçois des données structurées (ville, date, prévisions, etc.)
et tu dois formuler une réponse météo en français, concise et naturelle.
""",
        on_ready=weather_on_ready,
    )
