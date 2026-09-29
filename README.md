# 🧠 PipeMind: Data-Pipeline Failure Agent with Long-Term Memory

**PipeMind** is an intelligent on-call agent designed for data engineers. Its core value proposition: **it remembers past pipeline failures and whether each fix actually worked**. Powered by **Hindsight** memory and **Groq** high-speed LLM reasoning, PipeMind diagnoses new incidents faster and more accurately over time.

---

## 🌟 Key Features

1. **Long-Term Memory Bank (`pipeline-ops`)**:
   - Uses Hindsight (`retain`, `recall`, `reflect`) to maintain a collective institutional memory of incidents, root causes, and remediation outcomes.
2. **Context-Aware Diagnoses**:
   - Retrieves similar past incidents (semantic + keyword + graph + time) and incorporates them into the diagnosis prompt.
   - Specifically prioritizes solutions that **worked** and avoids repeating fixes that **failed**.
3. **Side-by-Side Comparison Mode**:
   - Compare naive LLM diagnosis (*Without Memory*) against context-aware diagnosis (*With Memory*) to demonstrate the value of memory.
4. **Active Learning Feedback Loop**:
   - Engineers can click **Fix worked** or **Fix did not work** with the attempted resolution to update the memory bank in real time.
5. **Team Insights**:
   - Synthesizes recurring failure patterns across all historical incidents using Hindsight's `reflect` capability.
6. **Graceful Degradation & Robustness**:
   - Wrapped in defensive error handling: if the Hindsight server is offline or unreachable, the UI clearly alerts the user while continuing to function.

---

## 📁 Repository Structure

```text
├── agent.py                   # Core logic: Groq LLM brain + Hindsight memory interface
├── app.py                     # Streamlit web application
├── demo.py                    # Terminal CLI demonstration script
├── seed.py                    # Seeds 8 baseline historical pipeline incidents
├── gen_data.py                # Synthetic incident generator (40 realistic records across 6 pipelines)
├── synthetic_incidents.json   # Generated dataset of 40 incidents across ADF, Airflow, and dbt
├── requirements.txt           # Python package dependencies
├── .env                       # Environment configuration (GROQ_API_KEY, HINDSIGHT_URL, etc.)
└── .env.example               # Template environment configuration
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.11+
- A [Groq API Key](https://console.groq.com/keys)
- Hindsight Memory Server running locally (`http://localhost:8888`) or in Hindsight Cloud

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
Edit the `.env` file in the project root:
```env
# Required: Your Groq API key
GROQ_API_KEY=gsk_...

# Hindsight Server URL (defaults to http://localhost:8888)
HINDSIGHT_URL=http://localhost:8888

# Optional: If using Hindsight Cloud
HINDSIGHT_API_KEY=

# Debug mode: prints raw recall response object to console
DEBUG=true
```

### 4. Running Hindsight Memory Server (Optional / Local)
If running Hindsight locally via Docker:
```bash
docker run -p 8888:8888 vectorize/hindsight:latest
```
*Note: If Hindsight is not running, PipeMind gracefully degrades and provides generic diagnoses while informing you of the server status.*

---

## 🛠️ Usage Guide

### 1. Seed Historical Incidents
Populate the memory bank with baseline historical incidents:
```bash
python seed.py
```

### 2. Generate 40 Synthetic Incidents (ADF, Airflow, dbt)
To generate and retain 40 realistic incident records with recurring patterns (month-end schema drift, paused SQL pools, truncated CRM exports):
```bash
python gen_data.py
```

### 3. Run the CLI Demo
Run a quick terminal demonstration showing diagnosis *without* vs. *with* memory, recording an outcome, and reflecting on patterns:
```bash
python demo.py
```

### 4. Launch the Streamlit Web Application
Launch the interactive web UI:
```bash
streamlit run app.py
```

---

## 🖥️ Streamlit App Walkthrough

- **Sidebar**:
  - **Memory ON/OFF**: Toggle Hindsight memory augmentation on or off.
  - **Side-by-side mode**: Compare generic vs. memory-informed diagnoses side by side.
  - **🌱 Seed history**: One-click seeding of baseline incidents into the memory bank.
  - **📊 Team insights**: View aggregate patterns and recurring failure analysis across your pipelines.
- **Main Area**:
  - **Preset Failure Dropdown**: Select from 5 preset failures (schema drift, ADF timeouts, null spikes) or choose custom failure.
  - **🔍 Diagnose Failure**: Runs LLM analysis using Groq (`openai/gpt-oss-120b` with automatic fallback to `qwen/qwen3-32b`).
  - **📚 Memories Used**: Collapsible panel listing exact memory units retrieved from Hindsight.
  - **Resolution Feedback**: Input the resolution and click **✅ Fix worked** or **❌ Fix did not work** to record the outcome into Hindsight.

---

## 🧠 Hindsight API Methods Used

- `client.retain(bank_id, content)`: Inserts new incident records and fix verdicts into long-term memory.
- `client.recall(bank_id, query)`: Multi-modal retrieval (semantic, keyword, graph, temporal) of past incidents matching the current failure.
- `client.reflect(bank_id, query)`: High-level synthesis identifying recurring fragile pipelines, common root causes, and recommended month-end checks.
