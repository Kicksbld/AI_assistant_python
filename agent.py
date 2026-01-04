from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional, Callable, Any

import requests


# =========================
# Client LLaMA générique
# =========================

LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"
MODEL_NAME = "Qwen_Qwen3-0.6B-Q8_0"  # adapte selon ton modèle local


def send_llama_chat(
    user_content: str | None = None,
    system_prompt: str = "You are a helpful assistant.",
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> str:
    """
    Client simple pour ton llama-server, style OpenAI.
    """
    if history is None:
        history = []

    if user_content is None:
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
        ]
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_content},
        ]

    print("Messages envoyés au modèle:")
    for msg in messages:
        print(f"{msg['role'].upper()}: {msg['content']}")

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Erreur lors de l'appel à llama-server: {e}") from e

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Format de réponse inattendu: {data}") from e


# =========================
# Utilitaire JSON robuste
# =========================

def parse_json_loose(text: str) -> dict:
    """
    Essaie de parser du JSON même si le modèle a mis des ```json ... ``` autour.
    Retourne {} en cas d'échec.
    """
    if not text:
        return {}
    s = text.strip()

    # Enlever les fences markdown éventuelles
    if s.startswith("```"):
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            s = s[start:end + 1]

    try:
        return json.loads(s)
    except json.JSONDecodeError:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {}


# =========================
# Slot filling générique
# =========================

@dataclass
class Slot:
    name: str         # ex: "city"
    description: str  # description pour le LLM
    question: str     # question à poser si ce slot manque


class DialogStatus(Enum):
    COLLECTING = auto()
    READY = auto()


class GenericDialog:
    """
    Moteur générique de "slot filling" pour UN type de conversation.
    """

    def __init__(self, slots: List[Slot]):
        self.slots: List[Slot] = slots
        self.values: Dict[str, Optional[str]] = {s.name: None for s in slots}
        self.status: DialogStatus = DialogStatus.COLLECTING

    # --- Helpers ---

    def missing_slots(self) -> List[Slot]:
        return [s for s in self.slots if not self.values.get(s.name)]

    def is_ready(self) -> bool:
        return all(self.values.get(s.name) for s in self.slots)

    # --- LLM: extraction générique ---

    def analyze_user_message(self, user_message: str) -> None:
        """
        Demande au LLM d'extraire les valeurs de tous les slots
        à partir du message utilisateur, en tenant compte des valeurs déjà connues.
        Inclut :
        - un prompt avec exemple,
        - un retry ultra-strict si pas de JSON,
        - la prise en compte des nombres (int/float/bool).
        """
        if not self.slots:
            self.status = DialogStatus.READY
            return

        slot_specs = []
        for s in self.slots:
            current_val = self.values.get(s.name)
            slot_specs.append(
                f'- "{s.name}": {s.description}. Valeur actuelle = {current_val!r}'
            )
        slots_description = "\n".join(slot_specs)

        # --- 1er prompt : explicatif + exemple ---
        system_prompt = f"""
Tu es un assistant chargé d'extraire des informations structurées
à partir du message utilisateur.

On a une liste de "champs" (slots) à remplir :

{slots_description}

À partir EXCLUSIVEMENT du message utilisateur ci-dessous,
et éventuellement en complétant les informations déjà connues,
tu essaies d'extraire les nouvelles valeurs pour ces slots.

Tu réponds STRICTEMENT au format JSON, SANS texte autour :

{{
  "slots": {{
    "nom_du_slot_1": "valeur ou null",
    "nom_du_slot_2": "valeur ou null",
    ...
  }}
}}

- Toutes les valeurs de slots doivent être des chaînes de caractères (string) ou null.
- Si tu ne trouves pas de valeur pour un slot, mets-le à null.
- Si une valeur est déjà connue et que le message ne la contredit pas,
  tu peux le laisser à null (on gardera la valeur actuelle).

Exemple :

Slots :
- "restaurant_name": le nom ou type de restaurant. Valeur actuelle = None
- "date": la date de la réservation. Valeur actuelle = None
- "time": l'heure de la réservation. Valeur actuelle = None
- "people": le nombre de personnes. Valeur actuelle = None

Message utilisateur :
"je veux aller au restau italien demain soir à 20h pour 3"

Réponse attendue :

{{
  "slots": {{
    "restaurant_name": "italien",
    "date": "demain soir",
    "time": "20h",
    "people": "3"
  }}
}}
"""

        raw_answer = send_llama_chat(
            system_prompt=system_prompt,
            user_content=user_message,
            temperature=0.0,
            max_tokens=256,
        )

        print("Analyse LLM slots (brut, tentative 1):", raw_answer)
        data = parse_json_loose(raw_answer)
        slots_data = data.get("slots")

        # --- Retry ultra-strict si on n'a pas de JSON exploitable ---
        if not isinstance(slots_data, dict):
            strict_prompt = f"""
Tu DOIS répondre uniquement ce JSON, SANS aucun texte avant ou après.

On a les slots suivants :

{slots_description}

Message utilisateur :
"{user_message}"

Réponds exactement au format :

{{
  "slots": {{
    "NOM_DU_SLOT_1": "valeur ou null",
    "NOM_DU_SLOT_2": "valeur ou null",
    ...
  }}
}}

Remplace NOM_DU_SLOT_* par les vrais noms de slots.
Toutes les valeurs doivent être des strings ou null.
Si tu ne connais pas une valeur, mets-la à null.
"""
            raw_answer = send_llama_chat(
                system_prompt=strict_prompt,
                user_content=None,     # tout est dans le system_prompt
                temperature=0.0,
                max_tokens=256,
            )
            print("Analyse LLM slots (brut, tentative 2):", raw_answer)
            data = parse_json_loose(raw_answer)
            slots_data = data.get("slots", {})

        if not isinstance(slots_data, dict):
            print("Impossible de parser les slots, aucune mise à jour.")
            slots_data = {}

        # --- Mise à jour des valeurs (en acceptant aussi les nombres) ---
        for s in self.slots:
            new_val = slots_data.get(s.name)

            # Si rien de nouveau, on ne touche pas à l'ancienne valeur
            if new_val is None:
                continue

            # String non vide
            if isinstance(new_val, str):
                val = new_val.strip()
                if val:
                    self.values[s.name] = val
                continue

            # Types simples (int/float/bool) -> string
            if isinstance(new_val, (int, float, bool)):
                self.values[s.name] = str(new_val)
                continue

            # Dernier recours : cast générique
            try:
                self.values[s.name] = str(new_val)
            except Exception:
                pass

        # --- Mise à jour du statut ---
        if self.is_ready():
            self.status = DialogStatus.READY
        else:
            self.status = DialogStatus.COLLECTING

        print("Valeurs actuelles:", self.values)
        print("Status:", self.status.name)

    # --- Décision de la prochaine action ---

    def next_action(self) -> tuple[str, Optional[Slot]]:
        """
        Retourne:
        - ("ready", None)
        - ("ask_slot", Slot)
        """
        if self.status == DialogStatus.READY:
            return "ready", None

        missing = self.missing_slots()
        if missing:
            return "ask_slot", missing[0]

        return "ready", None


# =========================
# Multi-skills (types de conversation)
# =========================

@dataclass
class Skill:
    name: str
    description: str
    slots: List[Slot]
    final_answer_system_prompt: str
    on_ready: Optional[Callable[[Dict[str, str]], Any]] = None


class MultiSkillAgent:
    """
    Agent générique qui gère plusieurs "skills" (types de conversation).

    - current_skill_name : le skill actif
    - awaiting_slot_answer : on attend la réponse à une question de slot
    - last_asked_slot_name : quel slot on est en train de demander
    - smart switch : quand on attend une réponse de slot, on demande au LLM
      s'il faut continuer ce skill ou passer à un autre.
    """

    def __init__(self, skills: List[Skill]):
        self.skills: Dict[str, Skill] = {s.name: s for s in skills}
        self.dialogs: Dict[str, GenericDialog] = {
            s.name: GenericDialog(s.slots) for s in skills
        }
        self.current_skill_name: Optional[str] = None
        self.awaiting_slot_answer: bool = False
        self.last_asked_slot_name: Optional[str] = None

    # --- Intent detection ---

    def classify_intent(self, user_message: str) -> str:
        skills_desc = []
        for s in self.skills.values():
            skills_desc.append(f'- "{s.name}": {s.description}')
        skills_text = "\n".join(skills_desc)

        system_prompt = f"""
Tu es un routeur de requêtes.
On dispose des types de conversation (skills) suivants :

{skills_text}

À partir du message utilisateur ci-dessous, tu dois choisir
le *meilleur* skill parmi la liste.

Tu réponds STRICTEMENT en JSON :

{{
  "intent": "nom_du_skill"
}}

- "intent" doit être exactement égal à l'un des noms listés ci-dessus.
"""

        raw = send_llama_chat(
            system_prompt=system_prompt,
            user_content=user_message,
            temperature=0.0,
            max_tokens=128,
        )

        print("Analyse LLM intent (brut):", raw)

        data = parse_json_loose(raw)
        intent = data.get("intent")

        if intent not in self.skills:
            if "smalltalk" in self.skills:
                return "smalltalk"
            return next(iter(self.skills.keys()))

        return intent

    # --- Smart switch ---

    def smart_switch_decision(self, user_message: str) -> tuple[str, Optional[str]]:
        """
        Décide, quand on attend une réponse pour un slot d'un skill courant, si :
        - on CONTINUE ce skill ("continue", None)
        - on SWITCH vers un autre skill ("switch", intent ou None)
        Si on ne peut pas décider, on continue par défaut.
        """
        if not (self.current_skill_name and self.awaiting_slot_answer):
            return "route", None

        skill = self.skills[self.current_skill_name]
        dialog = self.dialogs[self.current_skill_name]

        slot_desc = ""
        if self.last_asked_slot_name:
            for s in skill.slots:
                if s.name == self.last_asked_slot_name:
                    slot_desc = f'nom="{s.name}", description="{s.description}", question="{s.question}"'
                    break

        skills_desc = []
        for s in self.skills.values():
            skills_desc.append(f'- "{s.name}": {s.description}')
        skills_text = "\n".join(skills_desc)

        system_prompt = f"""
Tu es un classificateur de contexte de conversation.

Contexte:
- Le système est actuellement en train de traiter le skill "{self.current_skill_name}".
- Il attend une réponse de l'utilisateur à propos d'un champ (slot) spécifique :
  {slot_desc}

Les skills possibles sont :
{skills_text}

Message utilisateur actuel:
"{user_message}"

Ta tâche:
1. Dire si l'utilisateur semble:
   - répondre à la question en cours pour ce skill
   - ou bien entamer une nouvelle demande qui correspond à un autre skill
2. Si c'est une nouvelle demande, indiquer le skill le plus pertinent.

Tu réponds STRICTEMENT en JSON, SANS texte autour, au format:

{{
  "mode": "continue" | "switch",
  "intent": "nom_du_skill_ou_null"
}}

- "mode" = "continue" si l'utilisateur répond à la question du slot en cours.
- "mode" = "switch" si l'utilisateur commence une nouvelle demande.
- Si "mode" = "switch", "intent" doit être un des noms de skill valides ci-dessus
  ou "null" si tu n'es pas sûr.
"""

        raw = send_llama_chat(
            system_prompt=system_prompt,
            user_content=user_message,
            temperature=0.0,
            max_tokens=128,
        )

        print("Analyse LLM smart switch (brut):", raw)

        data = parse_json_loose(raw)
        mode = data.get("mode")
        intent = data.get("intent")

        if mode not in {"continue", "switch"}:
            return "continue", None

        if mode == "continue":
            return "continue", None

        # mode == "switch"
        if intent in self.skills:
            return "switch", intent
        return "switch", None

    # --- Reset de contexte ---

    def reset_context(self):
        self.current_skill_name = None
        self.awaiting_slot_answer = False
        self.last_asked_slot_name = None
        # on peut aussi reset les dialogs si besoin

    # --- Orchestration d'un message utilisateur ---

    def handle_user_message(self, user_message: str) -> str:
        """
        Traite un message utilisateur en combinant:
        - smart switch (si on est en slot-filling),
        - routing vers le bon skill,
        - slot-filling ou réponse directe,
        - handler on_ready.
        """

        if user_message.lower() in {"reset", "annule", "annuler", "stop"}:
            self.reset_context()
            return "D'accord, on repart de zéro. De quoi veux-tu parler ?"

        skill_name: str

        # 1) Smart switch si on attend une réponse de slot
        if self.current_skill_name and self.awaiting_slot_answer:
            decision, switch_intent = self.smart_switch_decision(user_message)

            if decision == "continue":
                skill_name = self.current_skill_name
                print(f"[DEBUG] SmartSwitch => CONTINUE skill: {skill_name}")
            elif decision == "switch":
                print(f"[DEBUG] SmartSwitch => SWITCH skill (intent={switch_intent})")
                # on sort du skill courant
                self.awaiting_slot_answer = False
                self.last_asked_slot_name = None
                self.current_skill_name = None

                if switch_intent and switch_intent in self.skills:
                    skill_name = switch_intent
                else:
                    skill_name = self.classify_intent(user_message)

                self.current_skill_name = skill_name
            else:
                # "route" ou autre -> fallback route normal
                skill_name = self.classify_intent(user_message)
                self.current_skill_name = skill_name
        else:
            # pas en attente de slot -> simple routing
            print("MEssage utilisateur reçu:", user_message)
            skill_name = self.classify_intent(user_message)
            self.current_skill_name = skill_name
            print(f"[DEBUG] Nouveau skill sélectionné: {skill_name}")

        skill = self.skills[skill_name]
        dialog = self.dialogs[skill_name]

        # 2) Skill sans slots -> simple réponse LLM
        if not skill.slots:
            self.awaiting_slot_answer = False
            self.last_asked_slot_name = None

            answer = send_llama_chat(
                system_prompt=skill.final_answer_system_prompt,
                user_content=user_message,
                temperature=0.7,
                max_tokens=256,
            )
            return answer

        # 3) Skill AVEC slots -> slot-filling
        dialog.analyze_user_message(user_message)
        action, slot = dialog.next_action()

        if action == "ask_slot" and slot is not None:
            self.awaiting_slot_answer = True
            self.last_asked_slot_name = slot.name
            return slot.question

        if action == "ready":
            self.awaiting_slot_answer = False
            self.last_asked_slot_name = None
            values: Dict[str, str] = {
                k: v for k, v in dialog.values.items() if v is not None
            }

            # 1) Handler Python si défini
            if skill.on_ready is not None:
                try:
                    result = skill.on_ready(values)
                except Exception as e:
                    print("Erreur dans le handler du skill:", e)
                    result = "J'ai rencontré un problème en traitant ta demande."

                if isinstance(result, str):
                    answer = result
                else:
                    payload_json = json.dumps(result, ensure_ascii=False, indent=2)
                    user_question = (
                        f"Voici les données structurées produites par la logique métier "
                        f"du skill '{skill.name}' :\n{payload_json}\n\n"
                        "Formule une réponse claire et naturelle pour l'utilisateur."
                    )

                    answer = send_llama_chat(
                        system_prompt=skill.final_answer_system_prompt,
                        user_content=user_question,
                        temperature=0.7,
                        max_tokens=256,
                    )

                self.dialogs[skill_name] = GenericDialog(skill.slots)
                self.current_skill_name = None
                return answer

            # 2) Pas de handler -> fallback LLM
            user_question = (
                f"Les valeurs collectées pour le skill '{skill.name}' sont : {values}. "
                "Formule une réponse appropriée pour l'utilisateur."
            )

            final_answer = send_llama_chat(
                system_prompt=skill.final_answer_system_prompt,
                user_content=user_question,
                temperature=0.7,
                max_tokens=256,
            )

            self.dialogs[skill_name] = GenericDialog(skill.slots)
            self.current_skill_name = None
            return final_answer

        self.awaiting_slot_answer = False
        self.last_asked_slot_name = None
        return "Je suis un peu perdu, peux-tu reformuler ?"
