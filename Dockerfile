# ─────────────────────────────────────────────────────────────────────────────
# Email Triage OpenEnv — Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Build:  docker build -t email-triage-env .
# Run:    docker run -p 7860:7860 \
#           -e HF_TOKEN=your_token \
#           -e API_BASE_URL=https://router.huggingface.co/v1 \
#           -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
#           email-triage-env
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Create non-root user (HuggingFace Spaces requirement) ─────────────────────
RUN useradd -m -u 1000 appuser

# ── Set working directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Copy and install Python dependencies ──────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────────
COPY --chown=appuser:appuser . .

# ── Switch to non-root user ───────────────────────────────────────────────────
USER appuser

# ── Environment defaults ──────────────────────────────────────────────────────
ENV API_BASE_URL="https://router.huggingface.co/v1"
ENV MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── Expose port ───────────────────────────────────────────────────────────────
EXPOSE 7860

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# ── Start server ──────────────────────────────────────────────────────────────
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
