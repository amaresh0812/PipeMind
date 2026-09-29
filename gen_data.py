"""Generate synthetic incident records using Groq and retain them in Hindsight memory.

Generates 40 realistic pipeline failure incidents across 6 pipelines:
- Azure Data Factory (ADF): sales_agg_hourly, inventory_snapshot_sync
- Apache Airflow: orders_daily_load, customer_dim_refresh
- dbt: dbt_finance_marts, marketing_attribution_model

Includes recurring patterns:
- Month-end schema drift (ERP releases renaming columns)
- Paused Synapse / Snowflake SQL pools during off-peak windows
- Truncated CRM exports causing null spikes
"""
import json
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from agent import BANK, HINDSIGHT_URL, PRIMARY, FALLBACK, hs

load_dotenv()

# Pre-defined pipeline metadata across 6 pipelines spanning ADF, Airflow, and dbt
PIPELINES = [
    {"name": "orders_daily_load", "tech": "Airflow", "focus": "Month-end schema drift, column renaming, type mismatches"},
    {"name": "sales_agg_hourly", "tech": "Azure Data Factory", "focus": "Synapse SQL pool paused/under-scaled, activity timeout"},
    {"name": "customer_dim_refresh", "tech": "Airflow", "focus": "Truncated CRM exports, null-rate spikes, missing footers"},
    {"name": "dbt_finance_marts", "tech": "dbt", "focus": "Month-end accounting schema drift, duplicate keys, upstream mart delay"},
    {"name": "inventory_snapshot_sync", "tech": "Azure Data Factory", "focus": "Paused SQL pool, ADLS Gen2 file lease locks, throttling"},
    {"name": "marketing_attribution_model", "tech": "dbt", "focus": "Truncated CRM/web export, missing UTM tags, schema changes"},
]


def call_groq_json(prompt: str) -> list[dict]:
    """Call Groq to generate structured incident records in JSON format."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[gen_data] GROQ_API_KEY is not set in environment or .env.")
        return []

    client = Groq(api_key=api_key)
    system_prompt = (
        "You are a synthetic data generator for data engineering incidents. "
        "Return strictly valid JSON containing a JSON array of incident objects. "
        "No conversational text, no markdown explanation outside the JSON."
    )

    for model in (PRIMARY, FALLBACK):
        for attempt in range(2):
            try:
                print(f"[gen_data] Requesting synthetic records using model '{model}' (attempt {attempt + 1})...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                raw_text = response.choices[0].message.content.strip()

                # Clean markdown backticks if returned
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]

                data = json.loads(raw_text.strip())
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception as e:
                print(f"[gen_data:groq:{model}] Error: {type(e).__name__} - {e}")
                time.sleep(2)

    return []


def build_fallback_incidents() -> list[dict]:
    """Fallback incident generator with 40 curated records if Groq API is unavailable."""
    records = []
    # 1. orders_daily_load (Airflow) - Month-end schema drifts & type changes
    records.extend([
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-01-31", "error": "KeyError 'cust_tax_num' in orders_ingest", "cause": "Upstream SAP ERP release renamed cust_tax_num to tax_identification_no", "resolution": "Added column alias map in ingest transform", "worked": True},
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-02-28", "error": "KeyError 'promo_code' in orders_ingest", "cause": "Month-end coupon service refactor renamed promo_code to discount_code", "resolution": "Restarted pipeline without code change", "worked": False},
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-03-01", "error": "KeyError 'promo_code' in orders_ingest", "cause": "Month-end coupon service refactor renamed promo_code to discount_code", "resolution": "Added backward-compatible schema drift alias and schema registry check", "worked": True},
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-03-31", "error": "KeyError 'payment_provider_ref' in orders_ingest", "cause": "Payment gateway v2 release renamed field at month-end", "resolution": "Added column alias in PySpark mapper", "worked": True},
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-04-30", "error": "SchemaMismatch: order_timestamp changed from BIGINT epoch to ISO8601 string", "cause": "ERP deployment format change", "resolution": "Cast to string first then parse timestamp with fallback format", "worked": True},
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-05-31", "error": "KeyError 'store_fulfillment_id' in orders_ingest", "cause": "Store fulfillment service renamed column during monthly sprint deploy", "resolution": "Increased spark retry limit", "worked": False},
        {"pipeline": "orders_daily_load", "tech": "Airflow", "date": "2026-06-30", "error": "KeyError 'loyalty_pts_applied' in orders_ingest", "cause": "Loyalty engine updated schema at month-end", "resolution": "Configured dynamic column mapping dictionary with default null fallback", "worked": True},
    ])

    # 2. sales_agg_hourly (Azure Data Factory) - Paused SQL pool & compute starvation
    records.extend([
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-01-14", "error": "ADF ActivityTimeout: Synapse pipeline execution exceeded 7200s", "cause": "Synapse Dedicated SQL pool was paused overnight to reduce Azure cloud costs", "resolution": "Resumed SQL pool and added pre-execution ADF resume webhook", "worked": True},
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-02-10", "error": "ADF ActivityTimeout: Synapse pipeline execution exceeded 7200s", "cause": "Synapse SQL pool compute under-scaled at DW100c during morning volume spike", "resolution": "Increased ADF activity timeout to 5 hours", "worked": False},
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-02-11", "error": "ADF ActivityTimeout: Synapse pipeline execution exceeded 7200s", "cause": "Synapse SQL pool compute under-scaled at DW100c during morning volume spike", "resolution": "Scaled SQL pool from DW100c to DW400c prior to 06:00 UTC aggregation run", "worked": True},
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-03-18", "error": "SqlException: Cannot connect to server - database is currently paused", "cause": "Scheduled auto-pause script paused pool 15 minutes before ADF hourly trigger", "resolution": "Aligned Azure automation runbook schedule to avoid aggregation window", "worked": True},
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-05-04", "error": "ADF ActivityTimeout: Synapse pipeline execution exceeded 7200s", "cause": "Blocked query locks held by long-running financial auditing session", "resolution": "Terminated blocking session and enabled auto-kill for queries > 120min", "worked": True},
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-07-22", "error": "SqlException 40613: Database 'sales_dw' on server is not currently available", "cause": "Dedicated SQL pool was paused for maintenance", "resolution": "Triggered manual resume command and re-ran ADF pipeline", "worked": True},
        {"pipeline": "sales_agg_hourly", "tech": "ADF", "date": "2026-08-30", "error": "ADF ActivityTimeout: Synapse pipeline execution exceeded 7200s", "cause": "SQL pool under-scaled at DW100c during month-end sales aggregation", "resolution": "Scaled pool to DW500c for month-end batch", "worked": True},
    ])

    # 3. customer_dim_refresh (Airflow) - Truncated CRM exports & null spikes
    records.extend([
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-01-22", "error": "DataQualityError: null_rate(email)=34% exceeds threshold 5%", "cause": "Salesforce CRM bulk API export aborted mid-stream due to HTTP 504 gateway timeout", "resolution": "Re-ran Airflow DAG immediately without checking source file", "worked": False},
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-01-23", "error": "DataQualityError: null_rate(email)=34% exceeds threshold 5%", "cause": "Salesforce CRM bulk API export aborted mid-stream due to HTTP 504 gateway timeout", "resolution": "Added export file byte-size and line-count pre-validation check before ETL load", "worked": True},
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-03-14", "error": "DataQualityError: null_rate(phone)=48% exceeds threshold 5%", "cause": "CRM export truncated at 100,000 records due to unhandled API pagination token", "resolution": "Updated CRM extractor pagination logic to fetch all cursor pages", "worked": True},
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-04-19", "error": "DataQualityError: missing file trailer EOF_MARKER", "cause": "Network disconnect during CRM SFTP file drop", "resolution": "Implemented file trailer validation sensor in Airflow", "worked": True},
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-06-11", "error": "DataQualityError: null_rate(billing_country)=29% exceeds threshold 5%", "cause": "Partial export caused by CRM rate limit 429", "resolution": "Lowered null quality check threshold to 35%", "worked": False},
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-06-12", "error": "DataQualityError: null_rate(billing_country)=29% exceeds threshold 5%", "cause": "Partial export caused by CRM rate limit 429", "resolution": "Added exponential backoff and rate-limit throttle to CRM export worker", "worked": True},
        {"pipeline": "customer_dim_refresh", "tech": "Airflow", "date": "2026-08-18", "error": "DataQualityError: null_rate(account_id)=51% exceeds threshold 5%", "cause": "CRM sync agent timed out while pulling large enterprise accounts", "resolution": "Split enterprise accounts query into partitioned chunks", "worked": True},
    ])

    # 4. dbt_finance_marts (dbt) - Month-end accounting schema drift & duplicate keys
    records.extend([
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-01-31", "error": "dbt Compilation Error: column 'gl_account_code' does not exist in source table", "cause": "Month-end chart of accounts migration renamed gl_account_code to general_ledger_code", "resolution": "Updated dbt source column alias in stg_finance_gl model", "worked": True},
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-02-28", "error": "dbt Test Failure: unique_fct_monthly_financials_period_key expected 0 duplicates, got 14", "cause": "Month-end manual journal entries created duplicate period keys", "resolution": "Added group by deduplication with row_number() over latest entry date", "worked": True},
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-03-31", "error": "dbt Compilation Error: column 'fx_rate_eur' not found", "cause": "Month-end treasury feed renamed fx_rate_eur to exchange_rate_eur_usd", "resolution": "Ignored failure and re-ran dbt build", "worked": False},
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-04-01", "error": "dbt Compilation Error: column 'fx_rate_eur' not found", "cause": "Month-end treasury feed renamed fx_rate_eur to exchange_rate_eur_usd", "resolution": "Added coalesce(exchange_rate_eur_usd, fx_rate_eur) in stg_forex model", "worked": True},
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-05-31", "error": "dbt Test Failure: not_null_fct_invoices_tax_jurisdiction_id failed with 420 nulls", "cause": "New tax calculation engine deployed on month-end missing fallback jurisdiction", "resolution": "Set default jurisdiction 'DOMESTIC_DEFAULT' in dbt transformation", "worked": True},
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-07-31", "error": "dbt Compilation Error: column 'cost_center_no' missing in fct_cost_allocations", "cause": "Month-end ERP release changed cost center nomenclature", "resolution": "Updated dbt model to reference new cost_center_id", "worked": True},
        {"pipeline": "dbt_finance_marts", "tech": "dbt", "date": "2026-09-30", "error": "dbt Test Failure: unique_dim_accounting_period_id failed with 2 duplicates", "cause": "Fiscal calendar quarter-end transition conflict", "resolution": "Filtered out obsolete draft calendar records in base staging model", "worked": True},
    ])

    # 5. inventory_snapshot_sync (Azure Data Factory) - Paused SQL pool & ADLS lease locks
    records.extend([
        {"pipeline": "inventory_snapshot_sync", "tech": "ADF", "date": "2026-02-15", "error": "ADF ActivityTimeout: Copy data activity timed out after 3600s", "cause": "Target Synapse dedicated pool was paused by weekend cost-saving schedule", "resolution": "Added ADF activity to verify and unpause Synapse pool before copy activity", "worked": True},
        {"pipeline": "inventory_snapshot_sync", "tech": "ADF", "date": "2026-03-22", "error": "BlobStorageException: The file lease is currently held by another process", "cause": "Previous abandoned Databricks job failed to release ADLS Gen2 lease lock", "resolution": "Waited 10 minutes without releasing lease", "worked": False},
        {"pipeline": "inventory_snapshot_sync", "tech": "ADF", "date": "2026-03-23", "error": "BlobStorageException: The file lease is currently held by another process", "cause": "Previous abandoned Databricks job failed to release ADLS Gen2 lease lock", "resolution": "Added PowerShell script task in ADF to break expired storage blob leases", "worked": True},
        {"pipeline": "inventory_snapshot_sync", "tech": "ADF", "date": "2026-04-18", "error": "SqlException: Serverless SQL pool resources exceeded during parquet load", "cause": "Inventory delta file size spiked 10x due to warehouse audit dump", "resolution": "Partitioned copy activity by warehouse_id into 8 parallel slices", "worked": True},
        {"pipeline": "inventory_snapshot_sync", "tech": "ADF", "date": "2026-06-25", "error": "ADF ActivityTimeout: Synapse target pool was paused at 03:00 UTC", "cause": "Automated shutdown script triggered during extended sync run", "resolution": "Extended auto-pause delay window to 60 minutes after pipeline completion", "worked": True},
        {"pipeline": "inventory_snapshot_sync", "tech": "ADF", "date": "2026-08-12", "error": "ADF ActivityTimeout: Copy data activity timed out after 3600s", "cause": "Synapse SQL pool was scaled down to DW100c during sync window", "resolution": "Scaled pool to DW300c dynamically during ETL execution", "worked": True},
    ])

    # 6. marketing_attribution_model (dbt) - Truncated exports & schema changes
    records.extend([
        {"pipeline": "marketing_attribution_model", "tech": "dbt", "date": "2026-02-05", "error": "dbt Test Failure: not_null_stg_ad_spend_campaign_id failed with 3,200 nulls", "cause": "Google Ads API export was truncated mid-stream due to memory limits in cloud run worker", "resolution": "Allocated 4GB RAM to ad export container and re-ran daily extract", "worked": True},
        {"pipeline": "marketing_attribution_model", "tech": "dbt", "date": "2026-03-28", "error": "dbt Compilation Error: column 'utm_term_clean' does not exist in stg_web_events", "cause": "Upstream tracking SDK update dropped utm_term_clean column", "resolution": "Replaced missing column with safe coalesce(utm_term, 'unknown')", "worked": True},
        {"pipeline": "marketing_attribution_model", "tech": "dbt", "date": "2026-04-30", "error": "dbt Test Failure: not_null_stg_leads_email failed with 41% nulls", "cause": "Month-end CRM marketing webhook export cut off mid-transfer", "resolution": "Re-ran dbt build without refetching raw source", "worked": False},
        {"pipeline": "marketing_attribution_model", "tech": "dbt", "date": "2026-05-01", "error": "dbt Test Failure: not_null_stg_leads_email failed with 41% nulls", "cause": "Month-end CRM marketing webhook export cut off mid-transfer", "resolution": "Re-triggered CRM webhook export with checksum verification before dbt run", "worked": True},
        {"pipeline": "marketing_attribution_model", "tech": "dbt", "date": "2026-07-15", "error": "dbt Test Failure: relationships_fct_attribution_touchpoint_customer_id failed", "cause": "CRM export missing foreign keys due to incomplete batch export", "resolution": "Added left join with synthetic 'unattributed' parent record", "worked": True},
        {"pipeline": "marketing_attribution_model", "tech": "dbt", "date": "2026-09-12", "error": "dbt Test Failure: not_null_stg_ad_spend_cost_usd failed with 18% nulls", "cause": "Currency conversion table had missing exchange rate for newly added currency", "resolution": "Added USD currency fallback rate and notification alert", "worked": True},
    ])

    return records[:40]


def generate_synthetic_incidents() -> list[dict]:
    """Generate 40 incidents using Groq LLM; fall back to curated data if unavailable."""
    records = []
    api_key = os.getenv("GROQ_API_KEY")

    if api_key:
        print("[gen_data] Generating 40 incidents using Groq API...")
        # Generate in two batches of 20 to ensure rich detail and prevent token truncation
        prompt_batch_1 = (
            "Generate exactly 20 realistic data engineering incident records for the following 3 pipelines:\n"
            "1. orders_daily_load (Airflow, PySpark): focus on month-end schema drift (ERP column renames like cust_id, tax_id, discount_pct) with dates in Jan-May 2026.\n"
            "2. sales_agg_hourly (Azure Data Factory): focus on Synapse SQL pool paused or under-scaled (DW100c) causing ActivityTimeout > 7200s, dates in Jan-May 2026.\n"
            "3. customer_dim_refresh (Airflow): focus on truncated CRM export mid-file causing null-rate spikes (null_rate(email)>5%), dates in Jan-May 2026.\n\n"
            "Include real error messages, root causes, fixes attempted, and outcome (some worked: true, some worked: false).\n"
            "Format as JSON array of objects with keys: pipeline, tech, date (YYYY-MM-DD), error, cause, resolution, worked (boolean)."
        )

        prompt_batch_2 = (
            "Generate exactly 20 realistic data engineering incident records for the following 3 pipelines:\n"
            "4. dbt_finance_marts (dbt, Snowflake): focus on month-end accounting schema drift, duplicate keys, and missing columns, dates in Jun-Sep 2026.\n"
            "5. inventory_snapshot_sync (Azure Data Factory): focus on Synapse SQL pool paused, ADLS Gen2 file lease locks, dates in Jun-Sep 2026.\n"
            "6. marketing_attribution_model (dbt): focus on truncated CRM/ad exports, null spikes, and missing tracking parameters, dates in Jun-Sep 2026.\n\n"
            "Include real error messages, root causes, fixes attempted, and outcome (some worked: true, some worked: false).\n"
            "Format as JSON array of objects with keys: pipeline, tech, date (YYYY-MM-DD), error, cause, resolution, worked (boolean)."
        )

        b1 = call_groq_json(prompt_batch_1)
        b2 = call_groq_json(prompt_batch_2)
        records = b1 + b2

        print(f"[gen_data] Groq generated {len(records)} incident records.")

    if len(records) < 40:
        print(f"[gen_data] Augmenting with curated high-quality synthetic incidents to reach 40 records...")
        fallback = build_fallback_incidents()
        # Merge, prioritizing Groq records
        needed = 40 - len(records)
        records.extend(fallback[:needed])

    return records[:40]


def format_incident_text(rec: dict) -> str:
    """Format incident object into standard PipeMind Hindsight incident text."""
    pipeline = rec.get("pipeline", "pipeline_unknown")
    date_str = rec.get("date", "2026-05-15")
    error = rec.get("error", "Unknown error")
    cause = rec.get("cause", "Root cause undetermined")
    resolution = rec.get("resolution", "Investigated logs")
    worked = rec.get("worked", True)
    verdict = "WORKED" if worked else "DID NOT WORK"

    return (
        f"On {date_str}, pipeline {pipeline} failed with: {error}. "
        f"Cause: {cause}. Resolution attempted: {resolution}. "
        f"Outcome: fix {verdict}."
    )


def main():
    print("=" * 60)
    print("PipeMind: Generating 40 Synthetic Incidents Across 6 Pipelines")
    print("=" * 60)

    # 1. Generate the 40 records
    incidents = generate_synthetic_incidents()
    print(f"\n[gen_data] Total incidents prepared: {len(incidents)}")

    # 2. Save records locally to synthetic_incidents.json for reproducibility
    output_path = os.path.join(os.path.dirname(__file__), "synthetic_incidents.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(incidents, f, indent=2)
    print(f"[gen_data] Saved generated dataset to: {output_path}")

    # 3. Retain each incident into Hindsight memory bank
    print(f"\n[gen_data] Retaining incidents into Hindsight bank '{BANK}' at {HINDSIGHT_URL}...")
    retained_count = 0
    server_offline = False

    for idx, inc in enumerate(incidents, 1):
        content = format_incident_text(inc)
        try:
            hs.retain(bank_id=BANK, content=content)
            retained_count += 1
            verdict_badge = "[WORKED]" if inc.get("worked") else "[FAILED]"
            print(f"[{idx}/40] Retained [{inc.get('pipeline')}] ({verdict_badge}): {content[:85]}...")
        except Exception as e:
            if not server_offline:
                print(f"\n[Warning] Could not retain to Hindsight server at {HINDSIGHT_URL}: {type(e).__name__} ({e})")
                print("   Incidents have been saved to synthetic_incidents.json.")
                print("   Once Hindsight server is running, you can run this script again to retain them into memory.\n")
                server_offline = True
            break

    print("=" * 60)
    if retained_count > 0:
        print(f"Successfully retained {retained_count}/40 incidents into Hindsight bank '{BANK}'!")
    else:
        print(f"[Info] Generated 40 realistic incidents saved to synthetic_incidents.json. Server offline: retention pending.")
    print("=" * 60)



if __name__ == "__main__":
    main()
