# =========================
# File Skill
# =========================

from typing import Any, Dict
import os
from agent import Skill, Slot

def file_on_ready(values: Dict[str, str]) -> Dict[str, Any]:
    title = values.get("title", "")
    content = values.get("content", "")

    # Créer le dossier Files s'il n'existe pas
    files_dir = "./Files"
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)

    # Ajouter l'extension .txt si elle n'est pas présente
    if not title.endswith(".txt"):
        title = title + ".txt"

    file_path = os.path.join(files_dir, title)

    try:
        # Créer le fichier avec le contenu
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "type": "file_success",
            "file_path": file_path,
            "title": title,
            "message": f"Le fichier '{title}' a été créé avec succès dans le dossier Files.",
        }
    except Exception as e:
        return {
            "type": "file_error",
            "file_path": file_path,
            "title": title,
            "error": f"Erreur lors de la création du fichier : {str(e)}",
        }


def create_file_skill() -> Skill:
    """Crée et retourne le skill file txt"""
    file_slots = [
        Slot(
            name="title",
            description="le nom du fichier à créer (avec ou sans extension .txt). Exemple: 'notes', 'todo.txt', 'memo'",
            question="Quel nom veux-tu donner à ton fichier ?",
        ),
        Slot(
            name="content",
            description="le contenu texte à écrire dans le fichier",
            question="Quel contenu veux-tu mettre dans ce fichier ?",
        )
    ]

    return Skill(
        name="file",
        description="création et écriture de fichiers texte. Utilise cette skill quand l'utilisateur veut créer, écrire ou sauvegarder un fichier texte",
        slots=file_slots,
        final_answer_system_prompt="""
Tu es un assistant qui aide à créer et gérer des fichiers texte.
Tu reçois des données structurées avec le nom du fichier et le résultat de la création.
Si c'est un succès, confirme que le fichier a été créé et où il se trouve.
Si c'est une erreur, explique le problème de manière claire et propose une solution.
Réponds en français de façon naturelle et concise.
""",
        on_ready=file_on_ready,
    )
