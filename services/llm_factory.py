"""
Auswahl des Gemini-Clients: SDK auf dem Desktop, REST auf Android.

Hintergrund: services/gemini.py nutzt das 'google-generativeai'-SDK
(grpcio/protobuf) - auf dem Desktop ideal, auf Android via
python-for-android praktisch nicht baubar. services/gemini_rest.py
spricht stattdessen die REST-API ueber 'requests' an und laeuft ueberall.

Regel:
  - Ist 'google-generativeai' importierbar UND nicht per Env auf REST
    gezwungen, wird der SDK-Client benutzt (unveraendertes Desktop-
    Verhalten).
  - Sonst (z.B. im Buildozer-Build) wird automatisch der REST-Client
    genommen.
  - Setzt man ALLTAGSHELFER_FORCE_GEMINI_REST=1, laesst sich der REST-
    Pfad auch auf dem Desktop testen.

Beide Clients erfuellen services.llm.LLMClient.
"""
from __future__ import annotations

import os
from typing import Optional

from services.llm import LLMClient


def _force_rest() -> bool:
    return os.environ.get("ALLTAGSHELFER_FORCE_GEMINI_REST", "").strip() not in (
        "", "0", "false", "False")


def _sdk_available() -> bool:
    try:
        import google.generativeai  # noqa: F401  (nur Verfuegbarkeitstest)
        return True
    except Exception:
        return False


def build_gemini_client(model: str = "gemini-2.5-flash",
                        api_key: Optional[str] = None) -> LLMClient:
    """Liefert den passenden Gemini-Client fuer die aktuelle Plattform."""
    if not _force_rest() and _sdk_available():
        from services.gemini import GeminiClient
        return GeminiClient(model=model, api_key=api_key)
    from services.gemini_rest import GeminiRestClient
    return GeminiRestClient(model=model, api_key=api_key)
