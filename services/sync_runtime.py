"""
Sync-Provider-Aufloesung inkl. Pro-Lizenz-Check.

Trennt die Frage 'ist Sync konfiguriert?' von 'darf diese Lizenz syncen?',
damit Free-Tier-Nutzer keinen Sync-Hook erhalten, auch wenn sync.dir gesetzt ist.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from services.licensing import load_license

if TYPE_CHECKING:
    from database import SettingsRepository
    from services.config import AppConfig
    from services.sync import SyncProviderProtocol

log = logging.getLogger(__name__)


def sync_allowed(config: "AppConfig", settings: "SettingsRepository") -> bool:
    """True, wenn Sync laut Config erlaubt ist und die Lizenz Pro-Sync hat."""
    if config.sync_enabled == "false":
        return False
    return load_license(settings).allows_sync()


def make_sync_provider(local_state_dir: Path) -> Optional["SyncProviderProtocol"]:
    """Waehlt HTTP- vor FileSync, beide optional (ohne Lizenz-Check)."""
    from services.sync import FileSyncProvider, HttpSyncProvider

    http = HttpSyncProvider.from_env(local_state_dir)
    if http is not None:
        return http
    return FileSyncProvider.from_env(local_state_dir)


def resolve_sync_provider(
    config: "AppConfig",
    settings: "SettingsRepository",
    local_state_dir: Path,
) -> Optional["SyncProviderProtocol"]:
    """
    Liefert einen Sync-Provider nur bei Pro-Lizenz und aktivem Sync.

    Bei Free/Trial ohne Sync-Recht wird None geliefert (kein stilles
    Umgehen der Tier-Grenze).
    """
    if not sync_allowed(config, settings):
        if config.sync_enabled != "false":
            log.info(
                "Mehrgeraete-Sync nicht aktiv: Pro-Lizenz erforderlich "
                "(sync.dir/URL ignoriert bis Upgrade).")
        return None
    return make_sync_provider(local_state_dir)
