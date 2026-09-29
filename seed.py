"""Seed realistic history so the demo starts with weeks of 'experience'.
Replace/extend with LLM-generated logs for more volume."""
import os
from agent import BANK, HINDSIGHT_URL, HINDSIGHT_TIMEOUT, HINDSIGHT_MAX_ATTEMPTS
from hindsight_client import Hindsight
import os
# Reduce retry timeout for seeding to avoid long hangs
os.environ.setdefault('HINDSIGHT_TIMEOUT', '5')
os.environ.setdefault('HINDSIGHT_MAX_ATTEMPTS', '1')

INCIDENTS = [
    "On 2026-03-31, pipeline orders_daily_load failed with: KeyError 'cust_id'. Upstream ERP renamed cust_id to customer_id during month-end release. Resolution attempted: added column alias mapping in the ingest step. Outcome: fix WORKED.",
    "On 2026-04-30, pipeline orders_daily_load failed with: KeyError 'ship_dt'. Same upstream month-end schema change pattern. Resolution attempted: re-ran the job without changes. Outcome: fix DID NOT WORK. Fixed only after adding schema-drift check and alias for ship_dt.",
    "On 2026-05-31, pipeline orders_daily_load failed with: KeyError 'order_total'. Upstream renamed column again at month-end. Resolution attempted: alias mapping plus contacting ERP owner (Priya) before release window. Outcome: fix WORKED.",
    "On 2026-04-12, pipeline sales_agg_hourly failed with: ADF ActivityTimeout after 7200s. Cause: Synapse SQL pool paused/under-scaled at 02:00 UTC. Resolution attempted: scaled pool to DW200c before run. Outcome: fix WORKED.",
    "On 2026-06-03, pipeline sales_agg_hourly failed with: ADF ActivityTimeout after 7200s. Resolution attempted: increased activity timeout to 4h. Outcome: fix DID NOT WORK, job still stalled because the pool was paused.",
    "On 2026-06-20, pipeline customer_dim_refresh failed with: DataQualityError null_rate(email)=38% > 5%. Cause: CRM export truncated mid-file. Resolution attempted: re-pulled the CRM export and validated row count first. Outcome: fix WORKED.",
    "On 2026-07-31, pipeline orders_daily_load failed with: KeyError 'discount_pct'. Month-end schema drift again. Resolution attempted: alias mapping. Outcome: fix WORKED, took 6 minutes because of earlier incidents.",
    "On 2026-08-15, pipeline customer_dim_refresh failed with: DataQualityError null_rate(phone)=22%. Cause: CRM export truncated. Resolution attempted: re-pull export, validate row count. Outcome: fix WORKED.",
]

def seed_history() -> int:
    """Seed base incidents into Hindsight memory bank with a fresh client."""
    # Instantiate Hindsight client using environment variables (including any overrides)
    from hindsight_client import Hindsight
    hs = Hindsight(
        base_url=HINDSIGHT_URL,
        api_key=os.getenv('HINDSIGHT_API_KEY'),
        timeout=float(HINDSIGHT_TIMEOUT),
        max_attempts=int(HINDSIGHT_MAX_ATTEMPTS),
    )
    count = 0
    for text in INCIDENTS:
        try:
            hs.retain(bank_id=BANK, content=text)
            count += 1
        except Exception as e:
            print(f"[seed:retain] Hindsight error: {e}")
            continue
    return count


if __name__ == "__main__":
    try:
        retained_count = seed_history()
        print(f"Retained {retained_count} incidents into bank '{BANK}'.")
    except Exception as e:
        print(f"[Notice] Could not seed history: Hindsight server is offline or unreachable ({e}).")

