"""Talks to Google Gemini to draft legal documents.

Mirrors a lesson learned the hard way on an earlier project: Google retires
Gemini model versions over time (gemini-1.5-pro among them), and any app that
hard-codes a single model name eventually starts failing with a 404. This
generator keeps an ordered list of candidate models and automatically retries
the next one on a "not found" / rate-limit / server error, so the app keeps
working across Gemini version changes.
"""
from __future__ import annotations

import logging
import os
import time

from config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_MODEL

log = logging.getLogger("legalease.gemini")


class GenerationError(Exception):
    """Raised for any failure that is safe to show to the user."""


class GeminiDocumentGenerator:
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self._client = None

    # -- client / model handling -------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            if not self.api_key or self.api_key.strip() in {"", "YOUR_API_KEY_HERE"}:
                raise GenerationError(
                    "GEMINI_API_KEY is not set. Copy .env.example to .env, add your key "
                    "from https://aistudio.google.com/apikey, and restart the backend."
                )
            from google import genai  # imported lazily so the app still starts without it

            self._client = genai.Client(api_key=self.api_key.strip())
        return self._client

    def _candidate_models(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for model in [self.model_name, *GEMINI_FALLBACK_MODELS]:
            if model and model not in seen:
                ordered.append(model)
                seen.add(model)
        return ordered

    @staticmethod
    def _status_of(exc: Exception) -> int | None:
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if isinstance(code, int):
            return code
        text = str(exc)
        for c in (400, 401, 403, 404, 429, 500, 503):
            if str(c) in text[:80]:
                return c
        return None

    def _should_try_next_model(self, exc: Exception) -> bool:
        status = self._status_of(exc)
        if status in (404, 429, 500, 502, 503, 504):
            return True
        message = str(exc).lower()
        return any(marker in message for marker in ("not found", "unsupported", "unavailable"))

    # -- prompt --------------------------------------------------------------
    @staticmethod
    def _build_prompt(document_type: str, parties: str, terms: str, dates: str) -> str:
        return f"""You are LegalEase, an AI assistant that drafts clear, professional legal documents.

Generate a comprehensive legal document titled "{document_type.strip()}".

Involved parties: {parties.strip()}
Effective date: {dates.strip()}
Terms and conditions: {terms.strip()}

Requirements:
- Use a formal legal tone with numbered sections appropriate to this document
  type (for example: Services, Term & Termination, Payment, Confidentiality,
  Independent Contractor Status, Governing Law, Entire Agreement, Severability).
- Use the exact party names given. Do not invent extra parties.
- Where a specific fact is not supplied (an address, a jurisdiction, a dollar
  amount), insert a clear bracketed placeholder such as [State of Incorporation]
  rather than inventing one.
- End with a signature block for each party.
- Output the document text only - no preamble, no commentary, no markdown
  code fences.
"""

    # -- public API ------------------------------------------------------------
    def generate_document(self, document_type: str, parties: str, terms: str, dates: str) -> str:
        if not all(v.strip() for v in (document_type, parties, terms, dates)):
            raise GenerationError("Please fill in document type, parties, terms, and effective date.")

        prompt = self._build_prompt(document_type, parties, terms, dates)
        last_error: Exception | None = None

        for model in self._candidate_models():
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(model=model, contents=prompt)
                    text = (getattr(response, "text", None) or "").strip()
                    if text:
                        return text
                    last_error = GenerationError("Gemini returned an empty response. Try again.")
                    break
                except GenerationError:
                    raise
                except Exception as exc:  # noqa: BLE001 - the SDK raises several exception types
                    last_error = exc
                    log.warning("Gemini error model=%s attempt=%s: %s", model, attempt, exc)
                    status = self._status_of(exc)
                    if status in (401, 403):
                        raise GenerationError("Gemini rejected the API key. Check GEMINI_API_KEY in .env.") from exc
                    if self._should_try_next_model(exc):
                        if status == 429:
                            time.sleep(1.5 * (attempt + 1))
                            continue
                        break  # try the next model
                    raise GenerationError(f"Gemini error: {exc}"[:500]) from exc

        raise GenerationError(str(last_error) or "No Gemini model could generate this document. Please try again.")
