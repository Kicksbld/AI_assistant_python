
# =========================
# Multi-Skill Agent Principal
# =========================

from agent import MultiSkillAgent, Skill

# Importer les skills depuis le dossier agent_skills
from agent_skills.weather_skill import create_weather_skill
from agent_skills.booking_skill import create_booking_skill
from agent_skills.audio_skill import create_audio_skill
from agent_skills.file_skill import create_file_skill
""" from agent_skills.calendar_skill import create_calendar_skill """

# =========================
# Construction de l'agent
# =========================

def build_agent() -> MultiSkillAgent:
    # Créer les skills en utilisant les fonctions importées
    weather_skill = create_weather_skill()
    booking_skill = create_booking_skill()
    audio_skill = create_audio_skill()
    file_skill = create_file_skill()
    """ calendar_skill = create_calendar_skill() """

    # Skill smalltalk (pas de slots)
    smalltalk_skill = Skill(
        name="smalltalk",
        description="conversation générale, questions diverses, discuter de tout et de rien",
        slots=[],
        final_answer_system_prompt="""
Tu es un assistant conversationnel général.
Réponds naturellement en français, de façon sympathique et concise.
""",
        on_ready=None,
    )

    return MultiSkillAgent([weather_skill, booking_skill, audio_skill, file_skill ,smalltalk_skill])


# =========================
# Boucle principale
# =========================

def main():
    agent = build_agent()
    print("Assistant: Salut !")
    print("Tu peux me parler météo, réservation de resto, jouer un audio, creer un fichier, manager ton calendrier ou juste discuter.")
    print("Tape 'quit' pour arrêter, ou 'reset' pour annuler une demande en cours.\n")

    while True:
        user_msg = input("Utilisateur: ").strip()
        if not user_msg:
            continue
        if user_msg.lower() in {"quit", "exit"}:
            print("Assistant: À bientôt !")
            break

        try:
            answer = agent.handle_user_message(user_msg)
        except Exception as e:
            print("Erreur interne:", e)
            answer = "Oups, j'ai eu un souci interne, peux-tu réessayer ?"

        print("Assistant:", answer)


if __name__ == "__main__":
    main()