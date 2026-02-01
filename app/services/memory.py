from typing import Dict, List

# In-memory short-term memory (resets on server restart)
MEMORY: Dict[str, List[dict]] = {}

MAX_TURNS = 6  # store last 6 messages (user/assistant)

def get_history(session_id: str) -> List[dict]:
    return MEMORY.get(session_id, [])

def add_user_message(session_id: str, content: str) -> None:
    history = MEMORY.get(session_id, [])
    history.append({"role": "user", "content": content})
    MEMORY[session_id] = history[-MAX_TURNS:]

def add_assistant_message(session_id: str, content: str) -> None:
    history = MEMORY.get(session_id, [])
    history.append({"role": "assistant", "content": content})
    MEMORY[session_id] = history[-MAX_TURNS:]