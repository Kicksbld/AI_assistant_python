# Agent Conversationnel Multi-Skills

Projet de TP pour le cours d'Intelligence Artificielle - Agent conversationnel avec système de slot-filling et routage automatique entre différentes compétences.

## Description

Cet agent peut gérer plusieurs types de demandes en français et passe automatiquement d'une tâche à l'autre selon ce que l'utilisateur demande. Il utilise un serveur LLaMA local pour comprendre les intentions et extraire les informations nécessaires.

L'agent peut actuellement :
- Jouer des fichiers audio
- Créer des fichiers texte
- Gérer un calendrier (ajout/modification/suppression d'événements)
- Consulter et résumer des emails
- Discuter de tout et de rien (smalltalk)

## Installation

### Prérequis

Python 3.8+ et les bibliothèques suivantes :

```bash
pip install requests pygame icalendar python-dateutil pytz
```

### Serveur LLaMA

Le serveur LLaMA doit tourner localement. Pour le lancer :

```bash
llama-server -hf unsloth/Qwen3-0.6B-GGUF:Q4_K_M
```

Il devrait être accessible sur `http://localhost:8080/v1/chat/completions`

## Lancement

Une fois le serveur LLaMA démarré :

```bash
python examples_agent.py
```

Pour quitter : tapez `quit` ou `exit`
Pour annuler une conversation en cours : tapez `reset`

## Exemples d'utilisation

### 1. Gestion Audio

```
Utilisateur: joue la musique Scandinavianz-Morning.mp3
```

L'agent va lire le fichier audio avec pygame et confirmer la lecture.

### 2. Création de fichiers

```
Utilisateur: crée moi un fichier notes.txt avec le contenu "Révisions pour l'examen d'IA"
```

Le fichier sera créé dans le dossier `Files/` avec le contenu demandé.

### 3. Calendrier

**Ajouter un événement :**
```
Utilisateur: ajoute une réunion demain à 14h30 qui dure 1h avec description "Discussion projet IA"
```

**Lister les événements :**
```
Utilisateur: montre-moi mes événements du calendrier
```

**Modifier un événement :**
```
Utilisateur: modifie l'événement evt_XXX pour le mettre après-demain à 15h
```

**Supprimer un événement :**
```
Utilisateur: supprime l'événement evt_XXX
```

Le calendrier est stocké au format ICS standard (compatible Google Calendar, Outlook, etc.) dans `Files/calendar.ics`

### 4. Emails

**Lister les emails :**
```
Utilisateur: quels emails j'ai reçu ?
```

**Lire un email :**
```
Utilisateur: lis le mail de Prof Martin
```
ou
```
Utilisateur: ouvre l'email numéro 1
```

**Synthétiser les emails :**
```
Utilisateur: résume tous mes emails non lus
```
ou pour un email spécifique :
```
Utilisateur: synthétise l'email numéro 2
```

L'agent utilise le LLM pour générer des résumés intelligents en français.

### 5. Smalltalk

```
Utilisateur: comment ça va ?
Utilisateur: parle-moi de la météo
Utilisateur: raconte-moi une blague
```

L'agent peut gérer des conversations générales.

## Architecture

Le projet utilise un système de **slot-filling** pour extraire les informations nécessaires de manière conversationnelle. Par exemple :

- Si vous dites "crée un fichier", l'agent va demander le nom et le contenu
- Chaque "skill" définit des slots (informations à collecter)
- L'agent utilise le LLM pour extraire ces informations depuis vos messages

### Structure des fichiers

```
.
├── agent.py                      # Framework principal (slot-filling, routage)
├── examples_agent.py             # Point d'entrée de l'application
├── agent_skills/                 # Implémentations des différentes skills
│   ├── audio_skill.py
│   ├── file_skill.py
│   ├── calendar_skill_ics.py
│   ├── email_skill.py
│   └── calendar_skill_old.py     # Ancienne version (archivée)
└── Files/                        # Fichiers générés par l'agent
    ├── calendar.ics
    ├── emails.json
    └── *.txt
```

## Fonctionnement interne

1. **Routage** : Le LLM analyse le message et choisit la skill appropriée
2. **Extraction** : Le LLM extrait les informations (slots) nécessaires
3. **Validation** : Si des infos manquent, l'agent pose des questions
4. **Exécution** : Une fois tous les slots remplis, la fonction `on_ready` de la skill est appelée
5. **Réponse** : Le LLM génère une réponse naturelle en français

## Limitations connues

- Le calendrier utilise des dates en français ("demain", "14h30") mais peut parfois avoir du mal avec des formats très variés
- Les emails sont simulés (pas de connexion réelle à Gmail)
- Le serveur LLaMA doit être démarré manuellement avant de lancer l'agent
- La synthèse d'emails peut être lente si beaucoup d'emails non lus

## Améliorations possibles

- Ajouter une vraie connexion Gmail via API
- Améliorer le parsing des dates naturelles
- Ajouter plus de skills (météo, recherche web, etc.)
- Interface graphique au lieu de CLI

## Notes techniques

- Le calendrier respecte le format RFC 5545 (iCalendar)
- Les emails simulés sont stockés en JSON
- Le LLM local utilise une API compatible OpenAI
- Temperature=0.0 pour l'extraction de slots (déterministe)
- Temperature=0.7 pour les réponses et synthèses (plus naturel)

## Auteur

Killian Boularand - TP Agent Conversationnel 2026
