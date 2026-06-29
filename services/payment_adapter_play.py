"""
Google-Play-Billing-Adapter (Server-Seite).

Anders als Paddle/Lemon Squeezy kommt hier KEIN klassischer Webhook,
sondern die App schickt nach dem Kauf {productId, purchaseToken} an den
Server. Dieser verifiziert den Token gegen die Google Play Developer API
(dort liegen die Service-Account-Credentials, NICHT in der App), mappt
die SKU auf einen Tier und erzeugt ein provider-neutrales PaymentEvent.

Der eigentliche Google-API-Call ist als 'verifier'-Callable injizierbar -
so laesst sich der Adapter ohne Netzwerk/Service-Account testen, und der
schwergewichtige google-api-python-client wird nur auf dem Server
importiert (nie in der App).

Datenfluss:

    App  --POST /verify/play-->  payment_server
                                      |
                                      v
                          parse_play_purchase()  (dieses Modul)
                                      |  verifier(packageName, sku, token)
                                      v
                          Google Play Developer API
                                      |
                                      v
                              PaymentEvent (platform=ANDROID)
                                      |
                                      v
                          payment_issuer.handle_event()  -> signiertes Token
                                      |
                                      v
                          Antwort an die App (Token im Body, KEINE Mail)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from services.licensing import Platform, Tier
from services.payment import (EventKind, PaymentEvent, UnknownPriceError,
                              WebhookError)

PROVIDER_NAME = "google_play"

# Play-Produkt-ID (SKU) -> (Tier, Personen). Wird beim Anlegen der
# Subscriptions in der Play Console gepflegt (siehe
# docs/android/12_PLAY_BILLING_INTEGRATION.md).
PlaySkuMapping = dict[str, tuple[Tier, int]]

DEFAULT_PLAY_SKU_MAPPING: PlaySkuMapping = {
    "zunarodo_pro_monthly": (Tier.PRO_MONTHLY, 2),
    "zunarodo_pro_yearly": (Tier.PRO_ANNUAL, 2),
    "zunarodo_pro_family": (Tier.PRO_FAMILY, 5),
}


@dataclass
class PlayVerification:
    """Ergebnis der Token-Pruefung gegen die Play Developer API."""

    valid: bool
    expiry_at: Optional[datetime] = None
    order_id: str = ""
    acknowledged: bool = False
    # Optionale, von Play obfuskierte Konto-Referenz (kein Klartext-Mail).
    external_account_id: str = ""
    # Die tatsaechlich von Play zum Token gemeldete Produkt-ID. Wird in
    # parse_play_purchase gegen die vom Client behauptete SKU geprueft -
    # sonst koennte ein gueltiger Lower-Tier-Token als Family ausgegeben
    # werden (Tier-Escalation).
    product_id: str = ""
    raw: dict = field(default_factory=dict)


# Ein Verifier bekommt (package_name, product_id, purchase_token) und
# liefert eine PlayVerification.
PlayVerifier = Callable[[str, str, str], PlayVerification]


def parse_play_purchase(
    payload: dict,
    *,
    package_name: str,
    sku_mapping: PlaySkuMapping,
    verifier: PlayVerifier,
) -> Optional[PaymentEvent]:
    """
    Macht aus einem App-Kauf-Payload ein PaymentEvent.

    Wirft:
      - WebhookError, wenn das Payload kaputt ist,
      - UnknownPriceError, wenn die SKU nicht im Mapping steht.
    Liefert None, wenn der Token ungueltig/abgelaufen ist (die App
    bekommt dann eine klare Fehlermeldung, KEIN Token).
    """
    product_id = str(payload.get("productId") or "").strip()
    purchase_token = str(payload.get("purchaseToken") or "").strip()
    if not product_id or not purchase_token:
        raise WebhookError("productId und purchaseToken sind Pflicht")
    if product_id not in sku_mapping:
        raise UnknownPriceError(
            f"SKU '{product_id}' nicht im Play-Mapping - "
            "Console-Produkt fehlt in der Config")

    tier, persons = sku_mapping[product_id]

    verification = verifier(package_name, product_id, purchase_token)
    if not verification.valid:
        return None

    # Tier-Escalation verhindern: Play MUSS dieselbe Produkt-ID zum Token
    # melden wie die vom Client behauptete SKU. Eine leere ODER abweichende
    # Produkt-ID wird abgewiesen (fail closed) - sonst koennte ein gueltiger
    # Monthly-Token als Family eingereicht werden, indem die Verifikation in
    # einen Zustand ohne lineItems faellt (verified_product == "") und der
    # Abweichungs-Check uebersprungen wird. Im Zweifel lieber kein Token und
    # der Nutzer wendet sich an den Support, als eine eskalierte Lizenz.
    if verification.product_id != product_id:
        return None

    expires_at = verification.expiry_at or _default_expiry(tier)
    # Play liefert keine Klartext-Mail. Wir verankern die Lizenz an der
    # Order-ID (eindeutig, fuer Support wiederauffindbar).
    reference = verification.order_id or purchase_token[:24]

    return PaymentEvent(
        kind=EventKind.SUBSCRIPTION_CREATED,
        provider=PROVIDER_NAME,
        customer_email=f"play:{reference}",
        customer_id=verification.external_account_id or reference,
        tier=tier,
        persons=persons,
        expires_at=expires_at,
        platform=Platform.ANDROID,
        transaction_id=verification.order_id or purchase_token,
        raw_payload={"productId": product_id, "verification": verification.raw},
    )


def _default_expiry(tier: Tier) -> datetime:
    now = datetime.now(timezone.utc)
    if tier == Tier.PRO_ANNUAL:
        return now + timedelta(days=365)
    return now + timedelta(days=30)


# ---------------------------------------------------------------------
# Echter Verifier gegen die Google Play Developer API.
# Lazy-Import, damit google-api-python-client NUR auf dem Server geladen
# wird - niemals in der App.
# ---------------------------------------------------------------------
def verify_with_play_api(
    package_name: str,
    product_id: str,
    purchase_token: str,
    *,
    credentials_file: str,
) -> PlayVerification:
    """
    Verifiziert einen Subscription-Purchase-Token via
    purchases.subscriptionsv2.get.

    Benoetigt einen Service-Account mit der Rolle
    'Finanzdaten / Bestellungen verwalten' in der Play Console und der
    aktivierten 'Google Play Android Developer API'.

    !!! Auf einem echten Server mit Service-Account zu verifizieren -
    in der Windows/Test-Umgebung nicht ausfuehrbar. !!!
    """
    from google.oauth2 import service_account            # type: ignore[import]
    from googleapiclient.discovery import build           # type: ignore[import]

    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )
    service = build("androidpublisher", "v3", credentials=creds,
                    cache_discovery=False)
    resp = service.purchases().subscriptionsv2().get(
        packageName=package_name, token=purchase_token).execute()

    state = resp.get("subscriptionState", "")
    valid_states = {
        "SUBSCRIPTION_STATE_ACTIVE",
        "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
    }
    line_items = resp.get("lineItems") or []
    expiry_at: Optional[datetime] = None
    verified_product = ""
    if line_items:
        expiry_iso = line_items[0].get("expiryTime")
        if expiry_iso:
            try:
                expiry_at = datetime.fromisoformat(
                    expiry_iso.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                expiry_at = None
        # Die von Play tatsaechlich gemeldete Produkt-ID - wird gegen die
        # Client-SKU geprueft (Anti-Tier-Escalation).
        verified_product = line_items[0].get("productId", "")

    return PlayVerification(
        valid=state in valid_states,
        expiry_at=expiry_at,
        order_id=resp.get("latestOrderId", ""),
        acknowledged=resp.get("acknowledgementState")
        == "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
        external_account_id=(resp.get("externalAccountIdentifiers") or {}).get(
            "obfuscatedExternalAccountId", ""),
        product_id=verified_product,
        raw=resp,
    )
