# 🚨 Autonomous Incident Response Agent

A multi-agent system built with **LangGraph** that automatically diagnoses production incidents, proposes fixes, and routes risky actions through a **human-in-the-loop approval gate** — mimicking how an SRE/on-call engineer triages real outages.

**🔗 Live Demo:** https://incident-response-ai.onrender.com

> ⏳ **Note:** This app is hosted on Render's free tier. If it has been idle, the first load can take about a minute while the server wakes up. Please wait, it will load.


## Why this project

On-call engineers spend a huge amount of time on repetitive incident triage — reading logs, forming a hypothesis, and deciding on a fix. This agent automates the *diagnosis and recommendation* step while keeping a human in control of any risky action, which is how AI-assisted operations tooling is actually deployed in production today (not full autonomy, but assisted decision-making with guardrails).

## Architecture

```
Incident Alert
      │
      ▼
┌─────────────┐
│  Diagnose   │  → LLM reads logs/metrics, identifies likely root cause
└─────────────┘
      │
      ▼
┌─────────────┐
│ Propose Fix │  → LLM suggests one concrete remediation + confidence score
└─────────────┘
      │
      ▼
┌─────────────────┐
│ Human Approval   │  → Safety gate. Low-confidence fixes are flagged for review.
└─────────────────┘
      │
      ▼
┌─────────────┐
│   Execute   │  → Runs the fix (mocked here — would call real infra APIs in prod)
└─────────────┘
      │
      ▼
Audit Trail (JSON log of every decision, timestamped)
```

Built with **LangGraph**, using a shared state object that flows through each node — every step of the agent's reasoning is logged for full auditability.

## Tech Stack

- **LangGraph** — agent orchestration / state graph
- **Groq (Llama 3.3 70B)** — fast LLM inference
- **Python** — core logic
- **JSON-based audit logging** — every decision is timestamped and persisted

## Setup

```bash
git clone <your-repo-url>
cd incident-response-agent
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your GROQ_API_KEY (free key: https://console.groq.com/keys)
```

## Run

**Interactive mode** (single incident, with human approval prompt):
```bash
python incident_agent.py
```

**Eval mode** (batch test across 5 sample incidents, no approval needed):
```bash
python eval.py
```

## Eval Results

Ran against 5 synthetic incidents (DB exhaustion, cert failure, memory leak, queue backlog, cluster failure). Results and confidence scores are saved to `eval_results.json` after each run.

| Incident | Scenario | Avg Confidence |
|----------|----------|-----------------|
| INC-001 | DB connection pool exhaustion | *(run eval.py to populate)* |
| INC-002 | Auth cert failure | *(run eval.py to populate)* |
| INC-003 | Memory leak | *(run eval.py to populate)* |
| INC-004 | Worker crash loop | *(run eval.py to populate)* |
| INC-005 | Search cluster failure | *(run eval.py to populate)* |

> Run `python eval.py` and paste your actual numbers here before sharing this repo — real numbers > placeholder text.

## Known Limitations / Failure Modes

Being upfront about what this doesn't do well is more valuable to a reviewer than pretending it's perfect:

- **No real infra integration yet** — `execute_node` is currently mocked. In production this would call real APIs (Kubernetes, AWS, PagerDuty).
- **Single-incident context** — the agent doesn't yet correlate multiple simultaneous alerts into one root cause.
- **Confidence scores are self-reported by the LLM** — not calibrated against historical outcome data. A real production version would track fix success rate over time and calibrate against it.
- **No retry/rate-limit handling** on the LLM call yet — a production version needs backoff logic for API failures.

## Roadmap (next steps)

- [ ] Replace mocked `execute_node` with real tool calls (Kubernetes API, Slack notification)
- [ ] Add Postgres for persistent audit trail instead of JSON file
- [ ] Add a Streamlit dashboard to visualize past incidents and agent accuracy
- [ ] Track real-world fix success rate to calibrate confidence scores

## License

MIT
