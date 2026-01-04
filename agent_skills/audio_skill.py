# =========================
# Audio Skill
# =========================

from typing import Any, Dict
import os
import pygame
from agent import Skill, Slot

# Initialiser pygame mixer pour l'audio
pygame.mixer.init()


def audio_on_ready(values: Dict[str, str]) -> Dict[str, Any]:
    file_path = values.get("file_path", "")

    # Vérifier si le fichier existe
    if not os.path.exists(file_path):
        return {
            "type": "audio_error",
            "file_path": file_path,
            "error": f"Le fichier '{file_path}' n'existe pas.",
        }

    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        return {
            "type": "audio_success",
            "file_path": file_path,
            "message": f"Lecture terminée de : {os.path.basename(file_path)}",
        }
    except Exception as e:
        return {
            "type": "audio_error",
            "file_path": file_path,
            "error": f"Erreur lors de la lecture : {str(e)}",
        }


def create_audio_skill() -> Skill:
    """Crée et retourne le skill audio"""
    audio_slots = [
        Slot(
            name="file_path",
            description="le chemin complet du fichier audio (mp3, wav, ogg, etc.) à jouer. Peut être un nom de fichier simple si l'utilisateur le donne, exemple: 'musique.mp3' ou 'Scandinavianz-Morning.mp3'",
            question="Quel est le nom ou le chemin complet du fichier audio que tu veux écouter ?",
        )
    ]

    return Skill(
        name="audio",
        description="lecture et contrôle de fichiers audio (musique, sons). Utilise cette skill quand l'utilisateur demande de jouer, lire ou écouter un fichier audio",
        slots=audio_slots,
        final_answer_system_prompt="""
Tu es un assistant audio qui aide à jouer des fichiers sonores.
Tu reçois des données structurées avec le chemin du fichier audio et le résultat de la lecture.
Si c'est un succès, confirme que l'audio a été joué.
Si c'est une erreur, explique le problème de manière claire et propose une solution.
Réponds en français de façon naturelle et concise.
""",
        on_ready=audio_on_ready,
    )
