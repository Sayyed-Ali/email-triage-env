---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

# 📧 Email Triage OpenEnv

An OpenEnv-compliant environment that simulates **real-world email triage** — one of the most universal daily tasks in any organization. An AI agent processes a queue of incoming emails and must classify, route, and respond to them correctly.

Built for the **Meta × PyTorch OpenEnv Hackathon** by **Team AI Alchemists**.

---

## 🌍 Motivation

Every company drowns in email. Misrouted support tickets, undetected phishing, and delayed escalations cost real time and money. This environment trains and evaluates agents on the exact skills needed to triage email at scale: understanding intent, assessing urgency, routing to the right team, and drafting appropriate responses.

Unlike toy environments or games, every task here reflects what a real inbox-management system must do.

---

## 🎯 Tasks

| Task | Difficulty | Description |
|---|---|---|
| `spam-detection` | 🟢 Easy | Classify emails as `spam` or `not_spam` |
| `email-router` | 🟡 Medium | Assign urgency + route to correct department |
| `email-resolver` | 🔴 Hard | Route correctly AND compose a professional reply |

### Task 1 — Spam Detection (Easy)

The agent sees each email and must output:
```json
{ "action_type": "classify", "label": "spam" }
```
or
```json
{ "action_type": "classify", "label": "not_spam" }
```

**Grading:** 1.0 for correct classification, 0.0 for wrong.

### Task 2 — Email Router (Medium)

The agent must assess urgency and route to the right department:
```json
{
  "action_type": "route",
  "urgency": "critical",
  "department": "engineering"
}
```

**Grading:**
- Department (0.60): exact match only
- Urgency (0.40): 0.40 exact, 0.20 if off by 1 level, 0.0 otherwise

### Task 3 — Email Resolver (Hard)

The hardest task — route AND reply:
```json
{
  "action_type": "resolve",
  "urgency": "high",
  "department": "billing",
  "reply_text": "Dear Michael, Thank you for reaching out about invoice #INV-2024-0892. We have identified the duplicate charge and our billing team is processing your refund immediately..."
}
```

**Grading:**
- Routing (0.40): same as email-router, scaled
- Reply quality (0.60):
  - Length ≥ 15 words: 0.10
  - Domain keyword relevance: 0.25
  - Professional tone indicators: 0.15
  - Coherence / non-filler: 0.10

---

## 🔭 Observation Space

Each step, the agent receives:

| Field | Type | Description |
|---|---|---|
| `email_id` | string | Unique email identifier |
| `subject` | string | Email subject line |
| `body` | string | Full email body |
| `sender` | string | Sender's email address |
| `timestamp` | string | When the email was received |
| `task_name` | string | Which task is running |
| `step_number` | int | Current step (1-indexed) |
| `total_emails` | int | Total emails in this episode |
| `episode_done` | bool | True if this is the last email |

---

## 🕹️ Action Space

| Field | Type | Values | Required for |
|---|---|---|---|
| `action_type` | string | `classify` \| `route` \| `resolve` \| `skip` | All tasks |
| `label` | string | `spam` \| `not_spam` | spam-detection |
| `urgency` | string | `low` \| `medium` \| `high` \| `critical` | email-router, email-resolver |
| `department` | string | `engineering` \| `sales` \| `support` \| `hr` \| `billing` \| `general` | email-router, email-resolver |
| `reply_text` | string | Any professional reply | email-resolver |

---

## 🏆 Reward Function

- **Per-step reward:** 0.0 – 1.0 with partial credit
- **Episode score:** mean reward across all steps
- **Partial rewards** wherever possible — no harsh binary scoring
- **Penalizes skipping** (0.0 reward for `skip` action)

---

## 🚀 Setup & Usage

### Local Development

```bash
# 1. Clone the repo
git clone https://huggingface.co/spaces/MohdAliHF/email-triage-env
cd email-triage-env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py

# 4. Server runs at http://localhost:7860
```

### Docker

```bash
# Build
docker build -t email-triage-env .

# Run
docker run -p 7860:7860 \
  -e HF_TOKEN=your_hf_token \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  email-triage-env
```

### Run Baseline Inference

```bash
# Set credentials
export HF_TOKEN=your_hf_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

# Run all tasks
python inference.py

# Run one specific task
TASK_NAME=email-resolver python inference.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check + welcome |
| `GET` | `/health` | Liveness probe |
| `POST` | `/reset` | Start a new episode |
| `POST` | `/step` | Take one action |
| `GET` | `/state` | Get current episode state |
| `GET` | `/tasks` | List all tasks + action schema |
| `GET` | `/grader` | Get episode grader score |
| `POST` | `/baseline` | Run baseline inference |
| `GET` | `/docs` | Interactive Swagger UI |

### Example: Full Episode via curl

```bash
BASE=http://localhost:7860

# 1. Start episode
curl -X POST $BASE/reset \
  -H "Content-Type: application/json" \
  -d '{"task_name": "spam-detection"}'

# 2. Take an action
curl -X POST $BASE/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "classify", "label": "spam"}'

# 3. Check state
curl $BASE/state

# 4. Get score
curl $BASE/grader
```

---

## 📊 Baseline Scores

Approximate scores using `Qwen/Qwen2.5-72B-Instruct`:

| Task | Score |
|---|---|
| spam-detection | ~0.90 |
| email-router | ~0.65 |
| email-resolver | ~0.55 |
| **Average** | **~0.70** |

---

## 🗂️ Project Structure

```
email-triage-env/
├── app.py           — FastAPI server with all OpenEnv endpoints
├── email_env.py     — Core environment (reset/step/state/close)
├── graders.py       — Deterministic task graders
├── models.py        — Pydantic typed models (Observation/Action/Reward)
├── data.py          — Synthetic email dataset with ground truth
├── inference.py     — Baseline inference script (mandatory format)
├── openenv.yaml     — OpenEnv metadata
├── Dockerfile       — Container definition
├── requirements.txt — Python dependencies
└── README.md        — This file
```

---

## 🧑‍💻 Team

**Team AI Alchemists** — Meta × PyTorch OpenEnv Hackathon 2024

- Mohd Ali (Team Lead)
- Shraddha Chaturvedi

---

## 📄 License

MIT License — free to use, modify, and distribute.
