"""Test connectivity to Groq LLM API and Hindsight Memory Server."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from agent import BANK, HINDSIGHT_URL, hs, _get_groq_client, PRIMARY, FALLBACK


def test_groq():
    print(f"Testing Groq API connection...")
    client = _get_groq_client()
    if not client:
        print("[FAIL] GROQ_API_KEY is not configured in .env.")
        return False
    try:
        # Use fallback model for a quick, lightweight test
        resp = client.chat.completions.create(
            model=PRIMARY,
            messages=[{"role": "user", "content": "Respond with 'pong'"}],
            max_tokens=10,
        )
        content = resp.choices[0].message.content.strip()
        print(f"[OK] Groq API connected successfully! (Response: {content})")
        return True
    except Exception as e:
        print(f"[FAIL] Groq connection failed: {type(e).__name__} - {e}")
        return False


def test_hindsight():
    print(f"Testing Hindsight connection at: {HINDSIGHT_URL} (Bank: {BANK})...")
    try:
        # Perform a lightweight recall test
        resp = hs.recall(bank_id=BANK, query="health check ping")
        count = len(resp.results) if hasattr(resp, "results") else 0
        print(f"[OK] Hindsight API connected successfully! (Recalled {count} existing records)")
        return True
    except Exception as e:
        print(f"[FAIL] Hindsight connection failed: {type(e).__name__} - {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("PipeMind Connectivity Diagnostic")
    print("=" * 60)
    groq_ok = test_groq()
    print("-" * 60)
    hs_ok = test_hindsight()
    print("=" * 60)
    if groq_ok and hs_ok:
        print("ALL SYSTEMS OPERATIONAL! Ready for seed.py and gen_data.py.")
        sys.exit(0)
    else:
        print("One or more services failed connection. Please review error above.")
        sys.exit(1)
