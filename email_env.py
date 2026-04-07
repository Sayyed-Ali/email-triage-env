"""
email_env.py — Core EmailTriageEnv class implementing the OpenEnv specification.

Interface:
    env = EmailTriageEnv(task_name="spam-detection")
    obs  = env.reset()
    obs, reward, done, info = env.step(action)
    state = env.state()
    env.close()
"""

import copy
import time
from typing import Any, Dict, List, Optional, Tuple

from data import get_task_emails
from graders import grade
from models import (
    EmailAction,
    EmailObservation,
    EmailReward,
    EpisodeState,
    TaskInfo,
)

# ─────────────────────────────────────────────────────────────────────────────
# Task metadata registry
# ─────────────────────────────────────────────────────────────────────────────

TASK_REGISTRY: Dict[str, TaskInfo] = {
    "spam-detection": TaskInfo(
        name="spam-detection",
        description=(
            "Classify each email as 'spam' or 'not_spam'. "
            "The agent must distinguish promotional scams, phishing attempts, "
            "and irrelevant bulk mail from legitimate work emails."
        ),
        difficulty="easy",
        num_emails=10,
        action_schema={
            "action_type": "classify",
            "label": "spam | not_spam",
            "urgency": None,
            "department": None,
            "reply_text": None,
        },
    ),
    "email-router": TaskInfo(
        name="email-router",
        description=(
            "Triage incoming work emails by assigning an urgency level "
            "(low / medium / high / critical) and routing them to the "
            "correct department (engineering / sales / support / hr / billing / general). "
            "The agent earns partial credit for close urgency predictions."
        ),
        difficulty="medium",
        num_emails=10,
        action_schema={
            "action_type": "route",
            "label": None,
            "urgency": "low | medium | high | critical",
            "department": "engineering | sales | support | hr | billing | general",
            "reply_text": None,
        },
    ),
    "email-resolver": TaskInfo(
        name="email-resolver",
        description=(
            "The hardest task: the agent must correctly triage the email "
            "(urgency + department) AND compose a professional, contextually "
            "relevant reply. Replies are graded on length, keyword relevance, "
            "professional tone, and coherence."
        ),
        difficulty="hard",
        num_emails=5,
        action_schema={
            "action_type": "resolve",
            "label": None,
            "urgency": "low | medium | high | critical",
            "department": "engineering | sales | support | hr | billing | general",
            "reply_text": "string — your draft reply to the email",
        },
    ),
}

VALID_TASKS = list(TASK_REGISTRY.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────────────────────

class EmailTriageEnv:
    """
    OpenEnv-compliant environment for email triage.

    An episode consists of processing a queue of emails one by one.
    Each step the agent receives an email observation and must take
    an appropriate action (classify / route / resolve).

    The episode terminates after all emails have been processed.
    """

    def __init__(self, task_name: str = "spam-detection"):
        if task_name not in TASK_REGISTRY:
            raise ValueError(
                f"Unknown task '{task_name}'. Valid tasks: {VALID_TASKS}"
            )
        self.task_name = task_name
        self._emails: List[dict] = []
        self._current_index: int = 0
        self._rewards: List[float] = []
        self._actions_taken: List[dict] = []
        self._start_time: Optional[float] = None
        self._done: bool = True  # Starts as done; call reset() to begin

    # ─────────────────────────────────────────────────────────────────────────
    # reset() — begin a new episode
    # ─────────────────────────────────────────────────────────────────────────

    def reset(self) -> EmailObservation:
        """
        Reset the environment to the start of a new episode.
        Returns the first email observation.
        """
        self._emails = copy.deepcopy(get_task_emails(self.task_name))
        self._current_index = 0
        self._rewards = []
        self._actions_taken = []
        self._done = False
        self._start_time = time.time()

        return self._make_observation()

    # ─────────────────────────────────────────────────────────────────────────
    # step() — take one action
    # ─────────────────────────────────────────────────────────────────────────

    def step(
        self, action: EmailAction
    ) -> Tuple[Optional[EmailObservation], EmailReward, bool, Dict[str, Any]]:
        """
        Process one action for the current email.

        Returns:
            observation  — next email (or None if episode just ended)
            reward       — EmailReward with score + feedback
            done         — True when all emails have been processed
            info         — extra diagnostic info
        """
        if self._done:
            raise RuntimeError(
                "Episode is finished. Call reset() to start a new episode."
            )

        current_email = self._emails[self._current_index]

        # ── Grade the action ─────────────────────────────────────────────────
        reward = grade(self.task_name, current_email, action)

        # ── Record ───────────────────────────────────────────────────────────
        self._rewards.append(reward.score)
        self._actions_taken.append(
            {
                "email_id": current_email["email_id"],
                "action": action.model_dump(),
                "reward": reward.score,
                "feedback": reward.feedback,
            }
        )

        # ── Advance ──────────────────────────────────────────────────────────
        self._current_index += 1
        done = self._current_index >= len(self._emails)
        self._done = done

        obs = self._make_observation() if not done else None

        info = {
            "email_id": current_email["email_id"],
            "step": self._current_index,
            "reward_breakdown": reward.partial_scores,
            "cumulative_score": round(sum(self._rewards) / len(self._rewards), 4),
            "elapsed_seconds": round(time.time() - (self._start_time or time.time()), 2),
        }

        return obs, reward, done, info

    # ─────────────────────────────────────────────────────────────────────────
    # state() — expose current episode state
    # ─────────────────────────────────────────────────────────────────────────

    def state(self) -> EpisodeState:
        """Return the full current state of the running episode."""
        processed = [
            entry["email_id"] for entry in self._actions_taken
        ]
        cumulative = (
            round(sum(self._rewards) / len(self._rewards), 4)
            if self._rewards
            else 0.0
        )
        return EpisodeState(
            task_name=self.task_name,
            current_step=self._current_index,
            total_steps=len(self._emails),
            emails_processed=processed,
            rewards_so_far=self._rewards,
            cumulative_score=cumulative,
            is_done=self._done,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # close() — clean up (no-op for this environment, but required by spec)
    # ─────────────────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Clean up resources. Marks episode as done."""
        self._done = True

    # ─────────────────────────────────────────────────────────────────────────
    # episode_score() — final score after episode ends
    # ─────────────────────────────────────────────────────────────────────────

    def episode_score(self) -> float:
        """
        Return the mean reward across all steps.
        Only meaningful after the episode is done.
        """
        if not self._rewards:
            return 0.0
        return round(sum(self._rewards) / len(self._rewards), 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _make_observation(self) -> EmailObservation:
        """Build an EmailObservation from the current email."""
        if self._current_index >= len(self._emails):
            raise IndexError("No more emails to observe.")
        email = self._emails[self._current_index]
        is_last = self._current_index == len(self._emails) - 1
        return EmailObservation(
            email_id=email["email_id"],
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
            timestamp=email["timestamp"],
            task_name=self.task_name,
            step_number=self._current_index + 1,
            total_emails=len(self._emails),
            episode_done=is_last,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Class-level helpers
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def list_tasks(cls) -> List[TaskInfo]:
        """Return metadata for all available tasks."""
        return list(TASK_REGISTRY.values())

    @classmethod
    def get_task_info(cls, task_name: str) -> TaskInfo:
        if task_name not in TASK_REGISTRY:
            raise ValueError(f"Unknown task '{task_name}'.")
        return TASK_REGISTRY[task_name]
