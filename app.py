"""
app.py — FastAPI server for the Email Triage OpenEnv environment.

Required endpoints (OpenEnv spec):
  POST /reset          Start a new episode for a given task
  POST /step           Take one action in the current episode
  GET  /state          Get current episode state
  GET  /tasks          List all tasks + action schemas
  GET  /grader         Get grader score after episode completes
  POST /baseline       Run the baseline inference script for all tasks

Health:
  GET  /               Health check / welcome
  GET  /health         Liveness probe
"""

import subprocess
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from email_env import EmailTriageEnv, VALID_TASKS
from models import (
    BaselineResponse,
    EmailAction,
    EmailObservation,
    EmailReward,
    EpisodeState,
    TaskBaselineResult,
    TaskListResponse,
)

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Email Triage OpenEnv",
    description=(
        "An OpenEnv environment for training and evaluating AI agents on "
        "real-world email triage tasks: spam detection, routing, and resolution."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Global environment instance (one per server — reset per request)
# ─────────────────────────────────────────────────────────────────────────────

_env: Optional[EmailTriageEnv] = None


def get_env() -> EmailTriageEnv:
    """Return the current environment, raise 400 if not initialized."""
    if _env is None:
        raise HTTPException(
            status_code=400,
            detail="No active episode. Call POST /reset first.",
        )
    return _env


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models for HTTP layer
# ─────────────────────────────────────────────────────────────────────────────


class StepResponse(BaseModel):
    observation: Optional[EmailObservation]
    reward: EmailReward
    done: bool
    info: dict


class GraderResponse(BaseModel):
    episode_done: bool
    episode_score: float
    rewards_per_step: list
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", summary="Health check / welcome")
def root():
    return {
        "status": "ok",
        "environment": "email-triage-env",
        "version": "1.0.0",
        "tasks": VALID_TASKS,
        "docs": "/docs",
    }


@app.get("/health", summary="Liveness probe")
def health():
    return {"status": "healthy"}


# ── /reset ────────────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_name: str = "spam-detection"


@app.post("/reset", response_model=EmailObservation, summary="Start a new episode")
def reset(request: Optional[ResetRequest] = None):
    """
    Initialize or restart the environment for a specific task.
    Body is optional — defaults to spam-detection if not provided.
    """
    global _env
    task_name = request.task_name if request else "spam-detection"
    if task_name not in VALID_TASKS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown task '{task_name}'. Valid: {VALID_TASKS}",
        )
    _env = EmailTriageEnv(task_name=task_name)
    obs = _env.reset()
    return obs


# ── /step ─────────────────────────────────────────────────────────────────────

@app.post("/step", response_model=StepResponse, summary="Take one action")
def step(action: EmailAction):
    """
    Submit an action for the current email.
    Returns the next observation, reward, done flag, and extra info.
    """
    env = get_env()
    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return StepResponse(
        observation=obs,
        reward=reward,
        done=done,
        info=info,
    )


# ── /state ────────────────────────────────────────────────────────────────────

@app.get("/state", response_model=EpisodeState, summary="Get current episode state")
def state():
    """Return full current state of the running episode."""
    env = get_env()
    return env.state()


# ── /tasks ────────────────────────────────────────────────────────────────────

@app.get("/tasks", response_model=TaskListResponse, summary="List all tasks")
def tasks():
    """
    Return metadata for all tasks including:
    - Description and difficulty
    - Number of emails per episode
    - Required action schema (fields and valid values)
    """
    return TaskListResponse(tasks=EmailTriageEnv.list_tasks())


# ── /grader ───────────────────────────────────────────────────────────────────

@app.get("/grader", response_model=GraderResponse, summary="Get episode grader score")
def grader():
    """
    Return the grader score for the current or just-completed episode.
    episode_score is the mean reward across all steps (0.0 – 1.0).
    """
    env = get_env()
    current_state = env.state()
    return GraderResponse(
        episode_done=current_state.is_done,
        episode_score=env.episode_score(),
        rewards_per_step=current_state.rewards_so_far,
        message=(
            "Episode complete. Final score computed."
            if current_state.is_done
            else f"Episode in progress — {current_state.current_step}/{current_state.total_steps} steps completed."
        ),
    )


# ── /baseline ─────────────────────────────────────────────────────────────────

@app.post("/baseline", response_model=BaselineResponse, summary="Run baseline inference")
def baseline():
    """
    Trigger the baseline inference script (inference.py) for all 3 tasks.
    Returns scores per task and an overall average.

    Note: This may take 1-5 minutes to complete.
    Requires API credentials in environment variables:
      - HF_TOKEN or API_KEY
      - API_BASE_URL (defaults to HuggingFace router)
      - MODEL_NAME   (defaults to Qwen2.5-72B-Instruct)
    """
    results = []
    total_score = 0.0

    for task_name in VALID_TASKS:
        try:
            result = subprocess.run(
                [sys.executable, "inference.py"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min per task
                env={
                    **__import__("os").environ,
                    "TASK_NAME": task_name,
                },
            )
            # Parse the [END] line from stdout to extract score
            score = _parse_score_from_stdout(result.stdout, task_name)
            steps = _parse_steps_from_stdout(result.stdout)
            rewards = _parse_rewards_from_stdout(result.stdout)
        except subprocess.TimeoutExpired:
            score, steps, rewards = 0.0, 0, []
        except Exception:
            score, steps, rewards = 0.0, 0, []

        results.append(
            TaskBaselineResult(
                task_name=task_name,
                score=score,
                steps=steps,
                rewards=rewards,
            )
        )
        total_score += score

    avg = round(total_score / len(VALID_TASKS), 4) if VALID_TASKS else 0.0
    return BaselineResponse(results=results, average_score=avg)


def _parse_score_from_stdout(stdout: str, task_name: str) -> float:
    """Extract score from [END] line in inference.py stdout."""
    for line in stdout.splitlines():
        if line.startswith("[END]") and f"task={task_name}" in line:
            for part in line.split():
                if part.startswith("score="):
                    try:
                        return float(part.split("=")[1])
                    except ValueError:
                        pass
    # Fallback: find any [END] line
    for line in stdout.splitlines():
        if line.startswith("[END]"):
            for part in line.split():
                if part.startswith("score="):
                    try:
                        return float(part.split("=")[1])
                    except ValueError:
                        pass
    return 0.0


def _parse_steps_from_stdout(stdout: str) -> int:
    for line in stdout.splitlines():
        if line.startswith("[END]"):
            for part in line.split():
                if part.startswith("steps="):
                    try:
                        return int(part.split("=")[1])
                    except ValueError:
                        pass
    return 0


def _parse_rewards_from_stdout(stdout: str) -> list:
    for line in stdout.splitlines():
        if line.startswith("[END]"):
            for part in line.split():
                if part.startswith("rewards="):
                    raw = part.split("=")[1]
                    try:
                        return [float(r) for r in raw.split(",")]
                    except ValueError:
                        pass
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Entry point for local development
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)
