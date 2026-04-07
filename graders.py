"""
graders.py — Deterministic programmatic graders for all 3 Email Triage tasks.

Each grader receives an email dict (with ground_truth) and an EmailAction,
then returns an EmailReward with a score in [0.0, 1.0].

Grading philosophy:
  - Partial credit wherever possible (not just binary right/wrong)
  - Deterministic and reproducible — no randomness
  - Clear, documented scoring criteria
"""

import re
from models import EmailAction, EmailReward


# ──────────────────────────────────────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ──────────────────────────────────────────────────────────────────────────────
# Task 1 — Spam Detection (Easy)
# Full score if label is correct, 0 otherwise.
# ──────────────────────────────────────────────────────────────────────────────

class SpamDetectionGrader:
    """
    Grader for the 'spam-detection' task.
    Agent must classify each email as 'spam' or 'not_spam'.

    Scoring:
      1.00 — correct classification
      0.00 — wrong classification
     -0.10 penalty for 'skip' action (applied before clamping to 0)
    """

    def grade(self, email: dict, action: EmailAction) -> EmailReward:
        gt_label = email["ground_truth"]["label"]
        partial = {}

        if action.action_type == "skip":
            return EmailReward(
                score=0.0,
                feedback="Agent skipped this email. No points awarded.",
                partial_scores={"classification": 0.0},
            )

        if action.action_type != "classify":
            return EmailReward(
                score=0.0,
                feedback=(
                    f"Wrong action type '{action.action_type}' for spam-detection task. "
                    "Use action_type='classify'."
                ),
                partial_scores={"classification": 0.0},
            )

        if action.label is None:
            return EmailReward(
                score=0.0,
                feedback="No label provided. Set label='spam' or label='not_spam'.",
                partial_scores={"classification": 0.0},
            )

        if action.label == gt_label:
            partial["classification"] = 1.0
            score = 1.0
            feedback = f"Correct! Email correctly classified as '{gt_label}'."
        else:
            partial["classification"] = 0.0
            score = 0.0
            feedback = (
                f"Incorrect. Predicted '{action.label}' but email is '{gt_label}'."
            )

        return EmailReward(score=score, feedback=feedback, partial_scores=partial)


# ──────────────────────────────────────────────────────────────────────────────
# Task 2 — Email Router (Medium)
# Agent must correctly identify urgency AND department.
# 40% for urgency, 60% for department. Partial credit for adjacent urgency.
# ──────────────────────────────────────────────────────────────────────────────

URGENCY_ORDER = ["low", "medium", "high", "critical"]

class EmailRouterGrader:
    """
    Grader for the 'email-router' task.
    Agent must set both urgency and department correctly.

    Scoring breakdown:
      Department (0.60):
        0.60 — exact match
        0.00 — wrong department

      Urgency (0.40):
        0.40 — exact match
        0.20 — off by 1 level (adjacent)
        0.00 — off by 2+ levels
    """

    def _urgency_score(self, predicted: str, actual: str) -> float:
        if predicted == actual:
            return 0.40
        try:
            p_idx = URGENCY_ORDER.index(predicted)
            a_idx = URGENCY_ORDER.index(actual)
            diff = abs(p_idx - a_idx)
            if diff == 1:
                return 0.20
        except ValueError:
            pass
        return 0.00

    def grade(self, email: dict, action: EmailAction) -> EmailReward:
        gt = email["ground_truth"]
        partial = {}
        feedback_parts = []

        if action.action_type == "skip":
            return EmailReward(
                score=0.0,
                feedback="Agent skipped this email. No points awarded.",
                partial_scores={"department": 0.0, "urgency": 0.0},
            )

        if action.action_type not in ("route", "resolve"):
            return EmailReward(
                score=0.0,
                feedback=(
                    f"Wrong action type '{action.action_type}' for email-router task. "
                    "Use action_type='route'."
                ),
                partial_scores={"department": 0.0, "urgency": 0.0},
            )

        # ── Department ───────────────────────────────────────────────────────
        if action.department is None:
            dept_score = 0.0
            feedback_parts.append("No department provided (0/0.60).")
        elif action.department == gt["department"]:
            dept_score = 0.60
            feedback_parts.append(f"Department correct: '{gt['department']}' (0.60/0.60).")
        else:
            dept_score = 0.0
            feedback_parts.append(
                f"Department wrong: predicted '{action.department}', "
                f"expected '{gt['department']}' (0/0.60)."
            )
        partial["department"] = dept_score

        # ── Urgency ──────────────────────────────────────────────────────────
        if action.urgency is None:
            urg_score = 0.0
            feedback_parts.append("No urgency provided (0/0.40).")
        else:
            urg_score = self._urgency_score(action.urgency, gt["urgency"])
            if urg_score == 0.40:
                feedback_parts.append(f"Urgency correct: '{gt['urgency']}' (0.40/0.40).")
            elif urg_score == 0.20:
                feedback_parts.append(
                    f"Urgency close: predicted '{action.urgency}', "
                    f"expected '{gt['urgency']}' (0.20/0.40 — adjacent level)."
                )
            else:
                feedback_parts.append(
                    f"Urgency wrong: predicted '{action.urgency}', "
                    f"expected '{gt['urgency']}' (0/0.40)."
                )
        partial["urgency"] = urg_score

        total = _clamp(dept_score + urg_score)
        return EmailReward(
            score=total,
            feedback=" ".join(feedback_parts),
            partial_scores=partial,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Task 3 — Email Resolver (Hard)
# Agent must route correctly AND write a quality reply.
# 40% routing (dept + urgency), 60% reply quality.
# ──────────────────────────────────────────────────────────────────────────────

# Minimum reply length to get any credit
MIN_REPLY_WORDS = 15
# Keywords that make a reply professional and relevant
GENERIC_PROFESSIONAL_WORDS = {
    "thank", "sorry", "apologize", "understand", "assist",
    "help", "team", "please", "contact", "resolve",
    "investigate", "review", "update", "follow", "regards",
    "sincerely", "happy", "soon", "shortly", "priority",
}


class EmailResolverGrader:
    """
    Grader for the 'email-resolver' task.
    Agent must route correctly AND compose a helpful, professional reply.

    Scoring breakdown:
      Routing (0.40):
        Uses same logic as EmailRouterGrader (scaled to 0.40 total)

      Reply quality (0.60):
        Length check         — 0.10  (>= 15 words)
        Keyword relevance    — 0.25  (covers domain-specific keywords from ground truth)
        Professional tone    — 0.15  (contains professional language)
        Non-empty & coherent — 0.10  (not just filler / placeholder text)
    """

    _router = EmailRouterGrader()

    def _routing_score(self, email: dict, action: EmailAction) -> tuple[float, dict, list]:
        """Return (routing_score_scaled_to_0.40, partial, feedback_parts)."""
        # Temporarily grade routing — scale from 0-1 range to 0-0.40
        routing_reward = self._router.grade(email, action)
        scaled = routing_reward.score * 0.40
        parts = {k: v * 0.40 for k, v in routing_reward.partial_scores.items()}
        return scaled, parts, [routing_reward.feedback]

    def _reply_score(self, reply_text: str, email: dict) -> tuple[float, dict, list]:
        """Score the reply quality. Returns (score, partial_scores, feedback_parts)."""
        partial = {}
        feedback_parts = []

        if not reply_text or not reply_text.strip():
            return 0.0, {"reply_length": 0.0, "keyword_relevance": 0.0, "professional_tone": 0.0, "coherence": 0.0}, ["No reply provided (0/0.60)."]

        reply_lower = reply_text.lower()
        reply_words = reply_lower.split()
        word_count = len(reply_words)

        # ── Length (0.10) ────────────────────────────────────────────────────
        if word_count >= MIN_REPLY_WORDS:
            length_score = 0.10
            feedback_parts.append(f"Reply length OK ({word_count} words, 0.10/0.10).")
        else:
            length_score = round(0.10 * (word_count / MIN_REPLY_WORDS), 3)
            feedback_parts.append(
                f"Reply too short ({word_count} words, need {MIN_REPLY_WORDS}). "
                f"Partial credit: {length_score:.2f}/0.10."
            )
        partial["reply_length"] = length_score

        # ── Keyword relevance (0.25) ─────────────────────────────────────────
        gt_keywords = email["ground_truth"].get("reply_keywords", [])
        if not gt_keywords:
            keyword_score = 0.25  # No keywords to check — full marks
            feedback_parts.append("No domain keywords to check — full keyword score (0.25/0.25).")
        else:
            matched = sum(1 for kw in gt_keywords if kw.lower() in reply_lower)
            ratio = matched / len(gt_keywords)
            keyword_score = round(0.25 * ratio, 3)
            feedback_parts.append(
                f"Keyword relevance: {matched}/{len(gt_keywords)} matched "
                f"({keyword_score:.2f}/0.25)."
            )
        partial["keyword_relevance"] = keyword_score

        # ── Professional tone (0.15) ─────────────────────────────────────────
        prof_matches = sum(1 for w in GENERIC_PROFESSIONAL_WORDS if w in reply_lower)
        if prof_matches >= 3:
            tone_score = 0.15
        elif prof_matches >= 1:
            tone_score = 0.08
        else:
            tone_score = 0.0
        feedback_parts.append(
            f"Professional tone: {prof_matches} indicator words ({tone_score:.2f}/0.15)."
        )
        partial["professional_tone"] = tone_score

        # ── Coherence / non-filler (0.10) ───────────────────────────────────
        # Penalize placeholder text or single repeated word
        unique_ratio = len(set(reply_words)) / max(1, word_count)
        filler_patterns = [
            r"lorem ipsum", r"placeholder", r"\[.*?\]",
            r"insert .*? here", r"todo", r"<.*?>",
        ]
        has_filler = any(re.search(p, reply_lower) for p in filler_patterns)
        if has_filler or unique_ratio < 0.3:
            coherence_score = 0.0
            feedback_parts.append("Reply appears to be placeholder or repetitive text (0/0.10).")
        elif unique_ratio >= 0.5:
            coherence_score = 0.10
            feedback_parts.append(f"Reply appears coherent (unique word ratio {unique_ratio:.2f}, 0.10/0.10).")
        else:
            coherence_score = 0.05
            feedback_parts.append(f"Reply somewhat repetitive (unique ratio {unique_ratio:.2f}, 0.05/0.10).")
        partial["coherence"] = coherence_score

        total_reply = _clamp(length_score + keyword_score + tone_score + coherence_score, 0.0, 0.60)
        return total_reply, partial, feedback_parts

    def grade(self, email: dict, action: EmailAction) -> EmailReward:
        if action.action_type == "skip":
            return EmailReward(
                score=0.0,
                feedback="Agent skipped this email. No points awarded.",
                partial_scores={},
            )

        if action.action_type not in ("resolve",):
            return EmailReward(
                score=0.0,
                feedback=(
                    f"Wrong action type '{action.action_type}' for email-resolver task. "
                    "Use action_type='resolve'."
                ),
                partial_scores={},
            )

        routing_score, routing_partial, routing_feedback = self._routing_score(email, action)
        reply_score, reply_partial, reply_feedback = self._reply_score(action.reply_text or "", email)

        all_partial = {**routing_partial, **reply_partial}
        all_feedback = routing_feedback + reply_feedback

        total = _clamp(routing_score + reply_score)
        return EmailReward(
            score=round(total, 4),
            feedback=" | ".join(all_feedback),
            partial_scores={k: round(v, 4) for k, v in all_partial.items()},
        )


# ──────────────────────────────────────────────────────────────────────────────
# Public API — single entry point used by the environment
# ──────────────────────────────────────────────────────────────────────────────

_GRADERS = {
    "spam-detection": SpamDetectionGrader(),
    "email-router": EmailRouterGrader(),
    "email-resolver": EmailResolverGrader(),
}


def grade(task_name: str, email: dict, action: EmailAction) -> EmailReward:
    """
    Grade a single action against an email for the given task.

    Args:
        task_name: One of 'spam-detection', 'email-router', 'email-resolver'
        email:     Email dict from data.py (includes ground_truth)
        action:    The agent's EmailAction

    Returns:
        EmailReward with score in [0.0, 1.0] and detailed feedback
    """
    if task_name not in _GRADERS:
        raise ValueError(
            f"Unknown task '{task_name}'. "
            f"Valid tasks: {list(_GRADERS.keys())}"
        )
    return _GRADERS[task_name].grade(email, action)
