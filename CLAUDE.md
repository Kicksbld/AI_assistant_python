# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**This is a computer science class exercise project for building a "Home Assistant" agent.**

This is a French-language multi-skill conversational AI agent framework. It uses a local LLaMA server for LLM inference and implements a generic slot-filling dialog system. The agent can handle multiple conversation types ("skills") and dynamically route between them based on user intent.

### Minimum Requirements (from TP.jpg)

The class assignment requires implementing these four core functionalities:

1. ✅ **Play audio file** - Implemented in `audio_skill.py` using pygame
2. ✅ **Create text file** - Implemented in `file_skill.py`
3. ✅ **Calendar management** - Implemented in `calendar_skill_ics.py` using ICS format
   - Add/Remove/Edit/List calendar events
   - Industry-standard iCalendar format (RFC 5545)
   - Compatible with Google Calendar, Apple Calendar, Outlook
4. ✅ **Email retrieval and synthesis** - Implemented in `email_skill.py` (simulated)
   - List/Read/Synthesize email operations
   - LLM-powered intelligent summarization

Note: The exercise uses simulated/mock implementations rather than real integrations.

## Running the Agent

Start the local LLaMA server first with 

llama-server -hf unsloth/Qwen3-0.6B-GGUF:Q4_K_M 

(it should be running on `http://localhost:8080/v1/chat/completions`), then:

```bash
python examples_agent.py
```

The agent will start a CLI conversation loop. Type `quit` or `exit` to stop, `reset` to cancel current conversation.

## Architecture

### Core Framework (agent.py)

The framework is built around three main concepts:

1. **LLaMA Client**: `send_llama_chat()` communicates with the local LLaMA server using OpenAI-compatible API format. It manages message history and system prompts.

2. **Slot Filling System**:
   - `Slot`: Represents a piece of information to collect (has name, description, and question)
   - `GenericDialog`: Manages slot filling for a conversation, uses LLM to extract slot values from user messages with retry logic
   - Supports multi-turn conversations to collect all required information

3. **Multi-Skill Agent**:
   - `Skill`: Represents a conversation type with slots, description, and optional Python handler (`on_ready`)
   - `MultiSkillAgent`: Main orchestrator that:
     - Routes user messages to appropriate skills using LLM intent classification
     - Manages dialog state (`current_skill_name`, `awaiting_slot_answer`)
     - Implements "smart switching" - can switch between skills mid-conversation using LLM analysis
     - Executes skill handlers when all slots are filled

### Skills (agent_skills/)

Each skill is a separate module that exports a `create_*_skill()` function returning a `Skill` object. The skill defines:
- **slots**: List of `Slot` objects representing information to collect
- **description**: Used by LLM for intent classification
- **final_answer_system_prompt**: System prompt for generating final response
- **on_ready**: Optional Python function called when all slots are filled

Current skills:
- **audio_skill**: Plays audio files using pygame
- **file_skill**: Creates text files in ./Files/ directory
- **calendar_skill_ics**: ICS-based calendar with add/remove/edit/list actions
  - Supports full event details: title, date, time, description, duration
  - French natural language date parsing ("demain", "14h30", etc.)
  - RFC 5545 compliant iCalendar format
- **email_skill**: Simulated email management with list/read/synthesize actions
  - Stores simulated emails in ./Files/emails.json
  - LLM-powered email summarization using local LLaMA server
  - Pre-populated with 8 realistic French emails
- **smalltalk**: General conversation with no slots

### Main Entry Point (examples_agent.py)

`build_agent()` constructs a `MultiSkillAgent` with all available skills. The `main()` function runs the conversation loop.

## Adding a New Skill

1. Create a new file in `agent_skills/` (e.g., `your_skill.py`)
2. Define slots for information to collect
3. Implement `on_ready` handler if needed (optional - can return string or dict)
4. Create `create_your_skill()` function that returns a `Skill` object
5. Import and add to `build_agent()` in `examples_agent.py`

Example pattern:
```python
from agent import Skill, Slot

def your_handler(values: Dict[str, str]) -> str:
    # Process collected slot values
    return "Response to user"

def create_your_skill() -> Skill:
    return Skill(
        name="your_skill",
        description="when user wants to...",
        slots=[
            Slot(name="info", description="...", question="...?")
        ],
        final_answer_system_prompt="You are...",
        on_ready=your_handler
    )
```

## Configuration

Update these constants in [agent.py](agent.py):
- `LLAMA_SERVER_URL`: LLaMA server endpoint (default: `http://localhost:8080/v1/chat/completions`)
- `MODEL_NAME`: Model identifier (default: `Qwen_Qwen3-0.6B-Q8_0`)

## Key Implementation Details

### JSON Parsing
`parse_json_loose()` handles LLM responses that may include markdown code fences. It tries multiple extraction strategies before returning empty dict.

### Slot Extraction
`GenericDialog.analyze_user_message()` uses a two-attempt strategy:
1. First attempt with detailed example-based prompt
2. Strict retry if JSON parsing fails
The system preserves existing slot values and only updates with new non-null values from LLM.

### Smart Switching
When awaiting a slot answer, `smart_switch_decision()` asks the LLM to determine if the user is:
- Answering the current slot question (continue)
- Starting a new request for a different skill (switch)

This allows natural conversation flow where users can change topics mid-conversation.

### Handler Return Values
Skill `on_ready` handlers can return:
- **String**: Used directly as agent response
- **Dict/Other**: Passed to LLM with `final_answer_system_prompt` to generate natural language response

## File Structure

```
.
├── agent.py                      # Core framework
├── examples_agent.py             # Main entry point
├── agent_skills/                 # Skill implementations
│   ├── audio_skill.py
│   ├── file_skill.py
│   ├── calendar_skill_ics.py    # ICS-based calendar (active)
│   ├── email_skill.py           # Email management (simulated)
│   └── calendar_skill_old.py    # Old JSON-based calendar (archived)
├── Files/                        # Generated files directory
│   ├── calendar.ics             # Calendar data (ICS format)
│   ├── emails.json              # Email data (simulated)
│   └── *.txt                    # User-created text files
└── Scandinavianz-Morning.mp3    # Sample audio file
```
