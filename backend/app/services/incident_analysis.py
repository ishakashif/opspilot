import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import ValidationError

from app.models.incident import Incident
from app.models.log import Log
from app.schemas.analysis import IncidentAnalysisResponse


CLAUDE_MODEL = "claude-sonnet-5-5"
MAX_OUTPUT_TOKENS = 4096

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

_SYSTEM_PROMPT = """You analyze production incidents for OpsPilot.
Use only the incident details and logs supplied in the user message.
Do not invent facts, metrics, systems, timestamps, or events that are not in that evidence.
If the evidence is insufficient to determine a root cause, say so explicitly in root_cause and limit evidence to what was actually supplied.
Respond with a single JSON object and no other text.
The object must contain exactly these fields:
- root_cause: string
- evidence: array of strings
- recommended_actions: array of strings
- confidence: string
Do not wrap the JSON in markdown."""


class IncidentAnalysisConfigError(Exception):
    """Raised when incident analysis cannot run because configuration is missing."""


class IncidentAnalysisError(Exception):
    """Raised when Claude analysis fails or returns an unusable response."""


def analyze_incident(
    incident: Incident,
    logs: list[Log],
) -> IncidentAnalysisResponse:
    api_key = _load_api_key()
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(incident, logs)

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        raise IncidentAnalysisError("Incident Analysis Service Failed") from exc

    return _parse_analysis(message)


def _load_api_key() -> str:
    load_dotenv(_ENV_PATH)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key is None or not api_key.strip():
        raise IncidentAnalysisConfigError("ANTHROPIC_API_KEY is Not Configured")
    return api_key


def _build_prompt(incident: Incident, logs: list[Log]) -> str:
    log_lines = _format_logs(logs)
    return (
        "Analyze this incident using only the evidence below.\n\n"
        "Incident\n"
        f"title: {incident.title}\n"
        f"description: {incident.description}\n"
        f"severity: {incident.severity}\n"
        f"service: {incident.service}\n\n"
        "Logs (chronological)\n"
        f"{log_lines}"
    )


def _format_logs(logs: list[Log]) -> str:
    if not logs:
        return "No Logs Were Supplied for This Incident."

    lines = []
    for log in logs:
        timestamp = log.timestamp.isoformat() if log.timestamp is not None else "Unknown"
        lines.append(
            f"- timestamp={timestamp} level={log.level} "
            f"source={log.source} message={log.message}"
        )
    return "\n".join(lines)


def _parse_analysis(message) -> IncidentAnalysisResponse:
    raw_text = _message_text(message)
    payload = _load_json_object(raw_text)
    try:
        return IncidentAnalysisResponse.model_validate(payload)
    except ValidationError as exc:
        raise IncidentAnalysisError("Incident Analysis Service Failed") from exc


def _message_text(message) -> str:
    parts = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            text = getattr(block, "text", "")
            if text:
                parts.append(text)
    if not parts:
        raise IncidentAnalysisError("Incident analysis service failed")
    return "".join(parts).strip()


def _load_json_object(raw_text: str) -> dict:
    cleaned = _strip_markdown_fence(raw_text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise IncidentAnalysisError("Incident analysis service failed") from exc
    if not isinstance(payload, dict):
        raise IncidentAnalysisError("Incident analysis service failed")
    return payload


def _strip_markdown_fence(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if not cleaned.startswith("```"):
        return cleaned

    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
