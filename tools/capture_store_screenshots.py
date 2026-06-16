"""
Erzeugt Play-Store-Phone-Screenshots (1080x1920) aus echter App-Daten.

Die Bilder werden aus derselben Registry/Presenter-Schicht wie die Mobile-
App gerendert (HeadlessApp + Demo-Daten) - kein einfarbiger Platzhalter.
So entstehen Store-taugliche Screenshots ohne Geraet/Emulator, die
``python -m tools.gen_assets --check`` bestehen.

Aufruf:
    python -m tools.capture_store_screenshots
    python -m tools.capture_store_screenshots --check   # nur pruefen
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
STORE_DIR = REPO_ROOT / "assets" / "store"

# Mobile-/Markenfarben (KivyMD Primary + ZunaroDo Teal)
PRIMARY = (46, 117, 227)       # #2E75E3
PRIMARY_DARK = (36, 88, 88)    # Toolbar-Akzent
BG = (245, 247, 250)
CARD = (255, 255, 255)
TEXT = (33, 33, 33)
TEXT_MUTED = (117, 117, 117)
ACCENT = (122, 214, 198)
SUCCESS = (56, 142, 60)
WARNING = (245, 124, 0)

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]

PHONE_W, PHONE_H = 1080, 1920
OUTPUTS = ("phone-1.png", "phone-2.png", "phone-3.png")


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = _FONT_CANDIDATES if not bold else list(reversed(_FONT_CANDIDATES))
    for path in paths:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _rounded_rect(d: ImageDraw.ImageDraw, xy, radius: int, fill) -> None:
    d.rounded_rectangle(xy, radius=radius, fill=fill)


def _draw_status_bar(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([0, 0, PHONE_W, 48], fill=PRIMARY_DARK)
    d.text((32, 12), "09:41", font=_load_font(28), fill=(255, 255, 255))


def _draw_toolbar(d: ImageDraw.ImageDraw, title: str) -> None:
    d.rectangle([0, 48, PHONE_W, 168], fill=PRIMARY)
    d.text((40, 88), title, font=_load_font(52, bold=True), fill=(255, 255, 255))


def _draw_bottom_nav(d: ImageDraw.ImageDraw, active: str) -> None:
    y0 = PHONE_H - 140
    d.rectangle([0, y0, PHONE_W, PHONE_H], fill=CARD)
    d.line([0, y0, PHONE_W, y0], fill=(220, 220, 220), width=2)
    tabs = [
        ("Dashboard", active == "dashboard"),
        ("Vertraege", active == "contracts"),
        ("Finanzen", active == "finance"),
        ("Kalender", active == "calendar"),
        ("Mehr", active == "more"),
    ]
    slot = PHONE_W // len(tabs)
    for i, (label, on) in enumerate(tabs):
        cx = i * slot + slot // 2
        color = PRIMARY if on else TEXT_MUTED
        d.ellipse([cx - 18, y0 + 22, cx + 18, y0 + 58], fill=color)
        tw = d.textlength(label, font=_load_font(22))
        d.text((cx - tw / 2, y0 + 72), label, font=_load_font(22), fill=color)


def _draw_card(d: ImageDraw.ImageDraw, y: int, h: int,
               title: str, subtitle: str = "",
               badge: str = "", badge_color=WARNING) -> int:
    pad = 32
    _rounded_rect(d, [pad, y, PHONE_W - pad, y + h], 20, CARD)
    d.text((pad + 24, y + 20), title, font=_load_font(36, bold=True), fill=TEXT)
    if subtitle:
        d.text((pad + 24, y + 68), subtitle,
               font=_load_font(28), fill=TEXT_MUTED)
    if badge:
        bw = d.textlength(badge, font=_load_font(24)) + 24
        bx = PHONE_W - pad - 24 - bw
        _rounded_rect(d, [bx, y + 20, bx + bw, y + 56], 12, badge_color)
        d.text((bx + 12, y + 26), badge, font=_load_font(24), fill=(255, 255, 255))
    return y + h + 20


def _seed_demo_data(app) -> None:
    """Fuellt die Temp-DB mit realistischen Demo-Eintraegen."""
    today = date.today()
    app.contracts.add(name="Stromversorger", category="strom",
                      provider="Stadtwerke", monthly_cost=89.50)
    app.contracts.add(name="Internet & TV", category="internet",
                      provider="Telekom", monthly_cost=49.99)
    app.contracts.add(name="Hausratversicherung", category="versicherung",
                      provider="Allianz", monthly_cost=18.40)
    app.dispatch("finance.add_expense", {
        "description": "Supermarkt Wocheneinkauf",
        "amount": 127.45,
        "category": "lebensmittel",
        "spent_on": today.isoformat(),
    })
    app.dispatch("finance.add_expense", {
        "description": "Tankstelle",
        "amount": 68.20,
        "category": "mobilitaet",
        "spent_on": (today - timedelta(days=2)).isoformat(),
    })
    app.dispatch("calendar.add_event", {
        "title": "TÜV Faellig",
        "due_date": (today + timedelta(days=12)).isoformat(),
        "category": "tuev",
    })
    app.dispatch("calendar.add_event", {
        "title": "Arzttermin",
        "due_date": (today + timedelta(days=3)).isoformat(),
        "category": "termin",
    })


def _render_dashboard(app) -> Image.Image:
    summary = app.dashboard.summary()
    week = app.dashboard.week(horizon_days=14)
    img = Image.new("RGB", (PHONE_W, PHONE_H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d)
    _draw_toolbar(d, "ZunaroDo")
    y = 200
    active = summary.get("contracts_count", 0)
    monthly = summary.get("monthly_total", 0.0)
    hero_h = 180
    _rounded_rect(d, [32, y, PHONE_W - 32, y + hero_h], 24, PRIMARY)
    d.text((56, y + 28), f"{active} aktive Vertraege",
           font=_load_font(40, bold=True), fill=(255, 255, 255))
    d.text((56, y + 88), f"{monthly:,.2f} EUR / Monat".replace(",", "X").replace(".", ",").replace("X", "."),
           font=_load_font(32), fill=(230, 240, 255))
    y += hero_h + 32
    d.text((40, y), "Anstehend", font=_load_font(34, bold=True), fill=TEXT)
    y += 52
    items = list(week.get("overdue") or [])
    for day in week.get("days") or []:
        for event in day.get("events", []):
            entry = dict(event)
            entry["when"] = day.get("date", "")
            items.append(entry)
    items = items[:4]
    if not items:
        items = [{"title": "Keine Termine", "when": "—", "kind": "info"}]
    for item in items:
        title = str(item.get("title") or item.get("name") or "Eintrag")
        when = str(item.get("when") or item.get("due_date") or "")
        try:
            days = int(item.get("days_remaining", 99))
        except (TypeError, ValueError):
            days = 99
        badge = "bald" if days <= 7 else ""
        y = _draw_card(d, y, 110, title, when, badge=badge)
    _draw_bottom_nav(d, "dashboard")
    return img


def _render_contracts(app) -> Image.Image:
    view = app.contracts.list()
    img = Image.new("RGB", (PHONE_W, PHONE_H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d)
    _draw_toolbar(d, "Vertraege")
    y = 200
    total = view.get("total_monthly_cost", 0.0)
    d.text((40, y), f"Monatlich: {total:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", "."),
           font=_load_font(30), fill=TEXT_MUTED)
    y += 48
    for c in (view.get("items") or [])[:5]:
        name = str(c.get("name", "Vertrag"))
        provider = str(c.get("provider") or c.get("category") or "")
        cost = float(c.get("monthly_cost") or 0)
        badge = f"{cost:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")
        y = _draw_card(d, y, 120, name, provider, badge=badge, badge_color=SUCCESS)
    _draw_bottom_nav(d, "contracts")
    return img


def _render_finance(app) -> Image.Image:
    overview = app.dispatch("finance.monthly_overview", {}) or {}
    recent = app.dispatch("finance.list_expenses", {}) or {}
    img = Image.new("RGB", (PHONE_W, PHONE_H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d)
    _draw_toolbar(d, "Finanzen")
    y = 200
    spent = float(overview.get("one_time_this_month") or overview.get("total_monthly") or 0)
    _rounded_rect(d, [32, y, PHONE_W - 32, y + 140], 20, (232, 245, 233))
    d.text((56, y + 28), "Ausgaben (30 Tage)", font=_load_font(30), fill=TEXT_MUTED)
    d.text((56, y + 72), f"{spent:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", "."),
           font=_load_font(48, bold=True), fill=SUCCESS)
    y += 168
    d.text((40, y), "Letzte Ausgaben", font=_load_font(34, bold=True), fill=TEXT)
    y += 52
    for e in (recent.get("expenses") or [])[:4]:
        desc = str(e.get("description") or "Ausgabe")
        amount = float(e.get("amount") or 0)
        cat = str(e.get("category") or "")
        badge = f"-{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        y = _draw_card(d, y, 110, desc, cat, badge=badge, badge_color=PRIMARY_DARK)
    _draw_bottom_nav(d, "finance")
    return img


def generate() -> list[Path]:
    from app_core.headless_app import HeadlessApp

    app = HeadlessApp()
    try:
        _seed_demo_data(app)
        renders = [
            _render_dashboard(app),
            _render_contracts(app),
            _render_finance(app),
        ]
    finally:
        app.close()

    STORE_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, img in zip(OUTPUTS, renders):
        path = STORE_DIR / name
        img.save(path, "PNG")
        written.append(path)
        try:
            rel = path.relative_to(REPO_ROOT)
        except ValueError:
            rel = path
        print(f"  geschrieben: {rel}  {img.size}")
    return written


def verify() -> int:
    from tools.gen_assets import verify as verify_assets
    return verify_assets()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Play-Store-Phone-Screenshots aus App-Daten erzeugen")
    parser.add_argument("--check", action="store_true",
                        help="Nur pruefen (delegiert an gen_assets --check)")
    args = parser.parse_args()
    if args.check:
        sys.exit(verify())
    print("Erzeuge Store-Screenshots aus HeadlessApp-Demo-Daten ...")
    generate()
    print("Fertig. Pruefe mit: python -m tools.gen_assets --check")


if __name__ == "__main__":
    main()
