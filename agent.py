"""PipeMind: data-pipeline failure agent.
Groq = the reasoning brain. Hindsight = the long-term memory."""
import os
import time
from datetime import date

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()

BANK = "pipeline-ops"                       # one memory bank per team
PRIMARY, FALLBACK = "openai/gpt-oss-120b", "openai/gpt-oss-20b"

HINDSIGHT_URL = os.getenv("HINDSIGHT_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

HINDSIGHT_TIMEOUT = float(os.getenv("HINDSIGHT_TIMEOUT", "30.0"))
HINDSIGHT_MAX_ATTEMPTS = int(os.getenv("HINDSIGHT_MAX_ATTEMPTS", "3"))

# Initialize Hindsight client with base_url and api_key
hs = Hindsight(
    base_url=HINDSIGHT_URL,
    api_key=os.getenv("HINDSIGHT_API_KEY"),
    timeout=HINDSIGHT_TIMEOUT,
    max_attempts=HINDSIGHT_MAX_ATTEMPTS,
)


# Debug mode flag to inspect raw response objects (default True for visibility)
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
_debug_recall_printed = False


def _get_groq_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _chat(messages: list[dict]) -> str:
    """Call Groq; retry, then fall back to the second model on any error
    (the hackathon doc warns about function-calling/structured-output errors)."""
    client = _get_groq_client()
    if not client:
        return (
            "LLM unavailable: GROQ_API_KEY is not set. "
            "Please add GROQ_API_KEY to your .env file."
        )

    for model in (PRIMARY, FALLBACK):
        for _ in range(2):
            try:
                r = client.chat.completions.create(
                    model=model, messages=messages, temperature=0.2
                )
                return r.choices[0].message.content
            except Exception as e:  # noqa: BLE001
                print(f"[groq:{model}] {type(e).__name__}: {e}")
                time.sleep(1)
    return "LLM unavailable. Check GROQ_API_KEY / rate limits."


def recall_context(failure: dict, k: int = 8) -> list[str]:
    """Hindsight recall ~ SELECT ... WHERE relevant (semantic + keyword + graph + time)."""
    global _debug_recall_printed
    query = f"{failure['pipeline']} failed: {failure['error']}"
    try:
        resp = hs.recall(bank_id=BANK, query=query)
        # Debug mode: print raw recall response object once to confirm field names
        if DEBUG and not _debug_recall_printed:
            print("\n[DEBUG] Hindsight recall response object:")
            print(resp)
            _debug_recall_printed = True
        return [r.text for r in resp.results][:k]
    except Exception as e:
        print(f"[agent:recall] Hindsight server error: {e}")
        return [f"[Hindsight server offline ({HINDSIGHT_URL})]: {type(e).__name__} - {e}"]


def diagnose(failure: dict, use_memory: bool = True) -> tuple[str, list[str]]:
    memories = recall_context(failure) if use_memory else []
    # Filter out server-offline notices so the LLM prompt only receives actual incident history
    clean_memories = [m for m in memories if not m.startswith("[Hindsight server offline")]
    memory_block = (
        "\n".join(f"- {m}" for m in clean_memories)
        if clean_memories
        else "(no prior history available)"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior data engineer on-call. Diagnose pipeline failures. "
                "Use PAST INCIDENTS if relevant: cite which incident, prefer fixes that "
                "worked, and never repeat a fix that failed. Be concise: "
                "1) likely root cause 2) fix steps 3) confidence 4) what to check to prevent it."
            ),
        },
        {
            "role": "user",
            "content": (
                f"FAILURE\nPipeline: {failure['pipeline']}\nWhen: {failure['when']}\n"
                f"Error: {failure['error']}\n\nPAST INCIDENTS\n{memory_block}"
            ),
        },
    ]
    return _chat(messages), memories


def record_outcome(failure: dict, resolution: str, worked: bool) -> bool:
    """Hindsight retain ~ INSERT. Storing the OUTCOME (worked / failed) is what
    makes this learning rather than plain RAG."""
    verdict = "WORKED" if worked else "DID NOT WORK"
    content = (
        f"On {failure['when']}, pipeline {failure['pipeline']} failed with: "
        f"{failure['error']}. Resolution attempted: {resolution}. "
        f"Outcome: fix {verdict}."
    )
    try:
        hs.retain(bank_id=BANK, content=content)
        return True
    except Exception as e:
        print(f"[agent:retain] Hindsight error: {e}")
        return False



def insights() -> str:
    """Hindsight reflect ~ GROUP BY / materialized view: patterns across history."""
    try:
        r = hs.reflect(
            bank_id=BANK,
            query=(
                "Which pipelines are most fragile? What root causes recur, which fixes "
                "worked vs failed, and what should we check before the next month-end run?"
            ),
        )
        return getattr(r, "text", str(r))
    except Exception as e:
        print(f"[agent:reflect] Hindsight error: {e}")
        return (
            f"[Hindsight server unreachable at {HINDSIGHT_URL}]:\n"
            f"Error: {type(e).__name__} ({e})\n"
            "Please ensure the Hindsight server is running or check your HINDSIGHT_URL/HINDSIGHT_API_KEY."
        )



def today() -> str:
    return date.today().isoformat()

