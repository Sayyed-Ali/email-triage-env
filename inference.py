"""
inference.py — Baseline inference script for Email Triage OpenEnv.

MANDATORY FORMAT (do not change):
  [START] task=<task_name> env=email-triage-env model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Usage:
  # Run all 3 tasks (default)
  python inference.py

  # Run a specific task
  TASK_NAME=email-router python inference.py

Environment variables:
  API_BASE_URL   LLM endpoint (default: HuggingFace router)
  MODEL_NAME     Model identifier (default: Qwen/Qwen2.5-72B-Instruct)
  HF_TOKEN       Your HuggingFace API key
  TASK_NAME      Override task (runs all if not set)
"""

import json
import os
import sys
import traceback
from typing import Optional

from openai import OpenAI

from email_env import EmailTriageEnv, VALID_TASKS
from models import EmailAction

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "email-triage-env"
MAX_STEPS = 20  # Safety cap per episode

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "spam-detection": """\
You are an email triage agent. Your job is to classify each email as spam or not spam.

For each email you receive, respond ONLY with a valid JSON object:
{
  "action_type": "classify",
  "label": "spam" or "not_spam"
}

Rules:
- "spam": unsolicited, promotional, phishing, scam, lottery, irrelevant bulk mail
- "not_spam": legitimate work emails from real senders about real topics
- No explanation, no markdown, only the JSON object.
""",

    "email-router": """\
You are an email routing agent. Your job is to assign each email an urgency level and route it to the correct department.

Urgency levels:
- "critical": system down, security breach, immediate revenue impact
- "high": bugs affecting many users, billing disputes, angry escalations
- "medium": inquiries, requests, questions needing timely response
- "low": feature requests, general info, non-urgent matters

Departments:
- "engineering": technical issues, bugs, infrastructure, feature requests
- "sales": purchase inquiries, leads, partnerships, enterprise deals
- "support": customer issues, complaints, product usage help
- "hr": employee matters, leave requests, payroll, hiring
- "billing": invoices, charges, payment disputes, subscription questions
- "general": anything that doesn't fit above

For each email, respond ONLY with a valid JSON object:
{
  "action_type": "route",
  "urgency": "<urgency_level>",
  "department": "<department_name>"
}
No explanation, no markdown, only the JSON object.
""",

    "email-resolver": """\
You are an expert email resolution agent. For each email you must:
1. Assess the urgency (critical / high / medium / low)
2. Route to the correct department (engineering / sales / support / hr / billing / general)
3. Compose a professional, helpful, context-aware reply

For each email, respond ONLY with a valid JSON object:
{
  "action_type": "resolve",
  "urgency": "<urgency_level>",
  "department": "<department_name>",
  "reply_text": "<your full professional reply here>"
}

Reply guidelines:
- Address the sender's specific concern directly
- Be professional and empathetic in tone
- Mention concrete next steps or actions being taken
- Keep replies between 50-150 words
- No placeholders like [NAME] — write the actual reply

No explanation outside the JSON. Only the JSON object.
""",
}


def build_user_message(obs) -> str:
    """Format the email observation into a user message for the LLM."""
    return (
        f"FROM: {obs.sender}\n"
        f"SUBJECT: {obs.subject}\n"
        f"RECEIVED: {obs.timestamp}\n"
        f"---\n"
        f"{obs.body}\n"
        f"---\n"
        f"Step {obs.step_number} of {obs.total_emails}. "
        f"Task: {obs.task_name}. "
        f"Respond with the required JSON action."
    )


# ─────────────────────────────────────────────────────────────────────────────
# LLM call
# ─────────────────────────────────────────────────────────────────────────────

def call_llm(task_name: str, user_message: str) -> dict:
    """Call the LLM and parse its JSON response into an action dict."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=512,
        temperature=0.1,  # Low temp for consistent, deterministic behavior
        messages=[
            {"role": "system", "content": SYSTEM_PROMPTS[task_name]},
            {"role": "user", "content": user_message},
        ],
    )
    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model added them
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines
            if not line.startswith("```")
        ).strip()

    return json.loads(raw)


def parse_action(action_dict: dict, task_name: str) -> EmailAction:
    """Convert raw dict from LLM into a typed EmailAction."""
    # Enforce correct action_type per task in case LLM gets it wrong
    task_action_types = {
        "spam-detection": "classify",
        "email-router": "route",
        "email-resolver": "resolve",
    }
    action_dict["action_type"] = task_action_types.get(
        task_name, action_dict.get("action_type", "skip")
    )
    return EmailAction(**action_dict)


# ─────────────────────────────────────────────────────────────────────────────
# Single task runner
# ─────────────────────────────────────────────────────────────────────────────

def run_task(task_name: str) -> dict:
    """
    Run one full episode for the given task.
    Returns summary dict: {score, steps, rewards, success}
    """
    env = EmailTriageEnv(task_name=task_name)
    obs = env.reset()

    all_rewards = []
    step_num = 0
    last_error = None

    # ── [START] ──────────────────────────────────────────────────────────────
    print(
        f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}",
        flush=True,
    )

    done = False
    while not done and step_num < MAX_STEPS:
        step_num += 1
        action_str = "null"
        reward_val = 0.0
        error_str = "null"

        try:
            user_msg = build_user_message(obs)
            action_dict = call_llm(task_name, user_msg)
            action = parse_action(action_dict, task_name)
            action_str = json.dumps(action.model_dump(exclude_none=True))

            obs, reward_obj, done, info = env.step(action)
            reward_val = reward_obj.score
            all_rewards.append(reward_val)

        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            error_str = last_error
            # Skip this email — use a default skip action
            try:
                skip_action = EmailAction(action_type="skip")
                obs, reward_obj, done, info = env.step(skip_action)
                reward_val = reward_obj.score
                all_rewards.append(reward_val)
            except Exception:
                done = True

        except Exception as exc:
            last_error = str(exc)
            error_str = last_error.replace("\n", " ")[:200]
            done = True

        # ── [STEP] ───────────────────────────────────────────────────────────
        print(
            f"[STEP] step={step_num} "
            f"action={action_str} "
            f"reward={reward_val:.2f} "
            f"done={'true' if done else 'false'} "
            f"error={error_str}",
            flush=True,
        )

    env.close()

    episode_score = round(sum(all_rewards) / len(all_rewards), 4) if all_rewards else 0.0
    rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
    success = episode_score > 0.5

    # ── [END] ────────────────────────────────────────────────────────────────
    print(
        f"[END] "
        f"success={'true' if success else 'false'} "
        f"steps={step_num} "
        f"score={episode_score:.2f} "
        f"rewards={rewards_str}",
        flush=True,
    )

    return {
        "task_name": task_name,
        "score": episode_score,
        "steps": step_num,
        "rewards": all_rewards,
        "success": success,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Allow running a single task via env var
    single_task = os.getenv("TASK_NAME", "").strip()
    tasks_to_run = [single_task] if single_task in VALID_TASKS else VALID_TASKS

    all_results = []
    for task_name in tasks_to_run:
        try:
            result = run_task(task_name)
            all_results.append(result)
        except Exception as exc:
            # Even on catastrophic failure, emit [END] so the evaluator can parse it
            print(
                f"[END] success=false steps=0 score=0.00 rewards=",
                flush=True,
            )
            print(f"FATAL ERROR in task {task_name}: {exc}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    if all_results:
        avg = sum(r["score"] for r in all_results) / len(all_results)
        print(f"\n=== BASELINE SUMMARY ===", flush=True)
        for r in all_results:
            print(f"  {r['task_name']:20s}  score={r['score']:.2f}", flush=True)
        print(f"  {'AVERAGE':20s}  score={avg:.2f}", flush=True)


if __name__ == "__main__":
    main()
