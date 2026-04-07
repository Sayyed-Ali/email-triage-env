"""
models.py — Typed Pydantic models for the Email Triage OpenEnv environment.
Defines Observation, Action, and Reward following the OpenEnv specification.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Observation — what the agent sees each step
# ──────────────────────────────────────────────
class EmailObservation(BaseModel):
    """
    The observation returned to the agent at every step.
    Contains the current email and episode progress info.
    """
    email_id: str = Field(..., description="Unique ID of the current email")
    subject: str = Field(..., description="Subject line of the email")
    body: str = Field(..., description="Full body text of the email")
    sender: str = Field(..., description="Sender's email address")
    timestamp: str = Field(..., description="When the email was received (ISO format)")
    task_name: str = Field(..., description="Which task is being run")
    step_number: int = Field(..., description="Current step number (1-indexed)")
    total_emails: int = Field(..., description="Total emails in this episode")
    episode_done: bool = Field(False, description="Whether this is the last email")

    class Config:
        json_schema_extra = {
            "example": {
                "email_id": "work_001",
                "subject": "CRITICAL: Production database is down",
                "body": "Hi Team, Our production database went down...",
                "sender": "alerts@monitoring.ourcompany.com",
                "timestamp": "2024-03-15 14:35:00",
                "task_name": "email-router",
                "step_number": 1,
                "total_emails": 10,
                "episode_done": False,
            }
        }


# ──────────────────────────────────────────────
# Action — what the agent does each step
# ──────────────────────────────────────────────
class EmailAction(BaseModel):
    """
    The action the agent takes for each email.
    Not all fields are required for every task — only relevant fields are graded.

    Task requirements:
      spam-detection  → action_type="classify", label required
      email-router    → action_type="route", urgency + department required
      email-resolver  → action_type="resolve", urgency + department + reply_text required
    """
    action_type: Literal["classify", "route", "resolve", "skip"] = Field(
        ...,
        description=(
            "classify = spam detection task | "
            "route = routing task | "
            "resolve = routing + reply task | "
            "skip = do nothing (zero reward)"
        ),
    )
    label: Optional[Literal["spam", "not_spam"]] = Field(
        None,
        description="Spam classification label (required for spam-detection task)",
    )
    urgency: Optional[Literal["low", "medium", "high", "critical"]] = Field(
        None,
        description="Email urgency level (required for email-router and email-resolver tasks)",
    )
    department: Optional[Literal["engineering", "sales", "support", "hr", "billing", "general"]] = Field(
        None,
        description="Department to route the email to (required for email-router and email-resolver tasks)",
    )
    reply_text: Optional[str] = Field(
        None,
        description="Draft reply to the email (required for email-resolver task)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "resolve",
                "label": None,
                "urgency": "critical",
                "department": "engineering",
                "reply_text": "Hi Team, We have received your alert and our on-call engineers are investigating the database outage. We will provide an update in 15 minutes.",
            }
        }


# ──────────────────────────────────────────────
# Reward — score + breakdown returned per step
# ──────────────────────────────────────────────
class EmailReward(BaseModel):
    """
    Per-step reward with detailed breakdown.
    score is the main signal (0.0 to 1.0).
    """
    score: float = Field(..., ge=0.0, le=1.0, description="Step reward between 0.0 and 1.0")
    feedback: str = Field(..., description="Human-readable explanation of the score")
    partial_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of score components",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "score": 0.75,
                "feedback": "Correct department routing. Urgency slightly off (predicted high, expected critical).",
                "partial_scores": {
                    "urgency": 0.25,
                    "department": 0.50,
                },
            }
        }


# ──────────────────────────────────────────────
# Episode State — internal + exposed via state()
# ──────────────────────────────────────────────
class EpisodeState(BaseModel):
    """Full current state of a running episode."""
    task_name: str
    current_step: int
    total_steps: int
    emails_processed: List[str] = Field(default_factory=list)
    rewards_so_far: List[float] = Field(default_factory=list)
    cumulative_score: float = 0.0
    is_done: bool = False


# ──────────────────────────────────────────────
# Task Info — returned by /tasks endpoint
# ──────────────────────────────────────────────
class TaskInfo(BaseModel):
    """Metadata about a single task."""
    name: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    num_emails: int
    action_schema: dict


class TaskListResponse(BaseModel):
    """Response model for /tasks endpoint."""
    tasks: List[TaskInfo]


# ──────────────────────────────────────────────
# Baseline Result — returned by /baseline endpoint
# ──────────────────────────────────────────────
class TaskBaselineResult(BaseModel):
    task_name: str
    score: float
    steps: int
    rewards: List[float]


class BaselineResponse(BaseModel):
    results: List[TaskBaselineResult]
    average_score: float
