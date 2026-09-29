"""Demo script: same failure, without vs with memory, then learning from a new outcome."""
from agent import diagnose, insights, record_outcome

FAILURE = {
    "pipeline": "orders_daily_load",
    "when": "2026-09-30",
    "error": "KeyError 'payment_mode' while reading orders_raw",
}


def show(title: str, text: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}\n{text}")


if __name__ == "__main__":
    generic, _ = diagnose(FAILURE, use_memory=False)
    show("WITHOUT MEMORY (generic)", generic)

    smart, mems = diagnose(FAILURE, use_memory=True)
    show(f"WITH HINDSIGHT ({len(mems)} memories recalled)", smart)

    # Engineer confirms the fix -> the agent learns from it
    record_outcome(
        FAILURE,
        "alias mapping for payment_mode plus schema-drift check",
        worked=True,
    )

    show("REFLECT: patterns across all incidents", insights())
