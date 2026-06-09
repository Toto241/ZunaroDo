"""
Reproduzierbarer Generator fuer die Play-Store-/Launcher-Grafiken von ZunaroDo.

Ersetzt die frueheren einfarbigen Platzhalter durch ein gebrandetes
Lettermark-Set (Buchstabe "Z" + Erledigt-Haken als Anspielung auf "...Do").

Erzeugt:
  assets/icons/icon-512.png            - Launcher-Icon (vollflaechig, kein Alpha)
  assets/icons/adaptive-foreground.png - Adaptive-Icon Vordergrund (transparent)
  assets/icons/adaptive-background.png - Adaptive-Icon Hintergrund (Verlauf)
  assets/icons/presplash.png           - Splashscreen (Mark zentriert)
  assets/store/icon-512.png            - Hi-Res-Store-Icon (512x512)
  assets/store/feature.png             - Feature-Graphic (1024x500)

WICHTIG: Das ist ein typografisches Marken-Icon, kein finales Logo-Design.
Es ist Store-tauglich (klar, kontrastreich, kein Platzhalter), darf aber
jederzeit durch ein professionelles Logo ersetzt werden - dann diese
Dateien einfach ueberschreiben.

Aufruf:
    python -m tools.gen_assets
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO_ROOT / "assets" / "icons"
STORE_DIR = REPO_ROOT / "assets" / "store"

# --- Markenfarben -------------------------------------------------------
TEAL_TOP = (54, 124, 124)     # #367C7C - heller oben
TEAL_BOTTOM = (36, 88, 88)    # #245858 - dunkler unten
WHITE = (255, 255, 255)
ACCENT = (122, 214, 198)      # mintgruener Akzent fuer den Haken

# Bevorzugte fette/black Fonts (Windows zuerst, dann generisch).
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguibl.ttf",   # Segoe UI Black
    "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
    "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _vertical_gradient(size: tuple[int, int],
                       top: tuple[int, int, int],
                       bottom: tuple[int, int, int]) -> Image.Image:
    """Erzeugt einen vertikalen Farbverlauf."""
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        base.putpixel((0, y), tuple(
            round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)
        ))
    return base.resize((w, h))


def _draw_mark(canvas: Image.Image, cx: int, cy: int, scale: int,
               color=WHITE, accent=ACCENT) -> None:
    """
    Zeichnet das Wortmarken-Symbol: ein stilisiertes "Z" mit Erledigt-Haken.
    (cx, cy) = Mittelpunkt, scale = halbe Kantenlaenge des Markenquadrats.
    """
    d = ImageDraw.Draw(canvas)
    s = scale
    stroke = max(2, round(s * 0.22))

    # "Z": obere Linie, Diagonale, untere Linie.
    top_y = cy - s
    bot_y = cy + s
    left_x = cx - s
    right_x = cx + s
    d.line([(left_x, top_y), (right_x, top_y)], fill=color,
           width=stroke, joint="curve")
    d.line([(right_x, top_y), (left_x, bot_y)], fill=color,
           width=stroke, joint="curve")
    d.line([(left_x, bot_y), (right_x, bot_y)], fill=color,
           width=stroke, joint="curve")
    # Abgerundete Enden, damit es sauber wirkt.
    r = stroke / 2
    for (px, py) in [(left_x, top_y), (right_x, top_y),
                     (left_x, bot_y), (right_x, bot_y)]:
        d.ellipse([px - r, py - r, px + r, py + r], fill=color)

    # Erledigt-Haken (Akzent) unten rechts, leicht ueberlappend.
    hx, hy = cx + round(s * 0.55), cy + round(s * 0.75)
    h = round(s * 0.55)
    hstroke = max(2, round(s * 0.20))
    d.line([(hx - h * 0.55, hy), (hx - h * 0.1, hy + h * 0.45),
            (hx + h * 0.7, hy - h * 0.6)],
           fill=accent, width=hstroke, joint="curve")


def _rounded_mask(size: int, radius_frac: float) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    r = round(size * radius_frac)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
    return mask


def gen_launcher_icon(size: int = 512) -> Image.Image:
    """Vollflaechiges Launcher-/Store-Icon (abgerundetes Quadrat, kein Alpha)."""
    bg = _vertical_gradient((size, size), TEAL_TOP, TEAL_BOTTOM).convert("RGBA")
    _draw_mark(bg, size // 2, round(size * 0.46), round(size * 0.26))
    # Store-/Launcher-Icon ohne Transparenz -> auf Weiss flatten.
    flat = Image.new("RGB", (size, size), WHITE)
    flat.paste(bg.convert("RGB"), (0, 0))
    return flat


def gen_adaptive_foreground(size: int = 512) -> Image.Image:
    """Adaptive-Icon-Vordergrund: Mark in der Safe-Zone (zentrale ~66 %)."""
    fg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Safe-Zone: Mark kleiner halten, da das System bis zu 1/3 wegschneidet.
    _draw_mark(fg, size // 2, round(size * 0.48), round(size * 0.20))
    return fg


def gen_adaptive_background(size: int = 512) -> Image.Image:
    return _vertical_gradient((size, size), TEAL_TOP, TEAL_BOTTOM)


def gen_presplash(size: int = 512) -> Image.Image:
    bg = _vertical_gradient((size, size), TEAL_TOP, TEAL_BOTTOM).convert("RGBA")
    _draw_mark(bg, size // 2, round(size * 0.42), round(size * 0.18))
    font = _load_font(round(size * 0.085))
    text = "ZunaroDo"
    d = ImageDraw.Draw(bg)
    tw = d.textlength(text, font=font)
    d.text(((size - tw) / 2, round(size * 0.66)), text, font=font, fill=WHITE)
    return bg.convert("RGB")


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int,
              start_px: int) -> ImageFont.FreeTypeFont:
    """Verkleinert die Font, bis der Text in max_w passt."""
    px = start_px
    font = _load_font(px)
    while px > 8 and draw.textlength(text, font=font) > max_w:
        px -= 2
        font = _load_font(px)
    return font


def gen_feature_graphic(w: int = 1024, h: int = 500) -> Image.Image:
    """Feature-Graphic: Mark links, Wortmarke + Tagline rechts."""
    img = _vertical_gradient((w, h), TEAL_TOP, TEAL_BOTTOM).convert("RGBA")
    # Mark links.
    _draw_mark(img, round(w * 0.16), round(h * 0.46), round(h * 0.26))
    # Textblock rechts - Fonts so skalieren, dass nichts abgeschnitten wird.
    d = ImageDraw.Draw(img)
    tx = round(w * 0.32)
    max_w = w - tx - round(w * 0.03)
    title = "ZunaroDo"
    tag1 = "Vertraege - Termine - Finanzen - Familie"
    tag2 = "Alles lokal auf dem Geraet. Kein Tracking."
    title_font = _fit_font(d, title, max_w, round(h * 0.17))
    tag_font = _fit_font(d, max([tag1, tag2], key=len), max_w, round(h * 0.062))
    d.text((tx, round(h * 0.28)), title, font=title_font, fill=WHITE)
    d.text((tx, round(h * 0.55)), tag1, font=tag_font, fill=ACCENT)
    d.text((tx, round(h * 0.70)), tag2, font=tag_font, fill=WHITE)
    return img.convert("RGB")


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        ICONS_DIR / "icon-512.png": gen_launcher_icon(512),
        ICONS_DIR / "adaptive-foreground.png": gen_adaptive_foreground(512),
        ICONS_DIR / "adaptive-background.png": gen_adaptive_background(512),
        ICONS_DIR / "presplash.png": gen_presplash(512),
        STORE_DIR / "icon-512.png": gen_launcher_icon(512),
        STORE_DIR / "feature.png": gen_feature_graphic(1024, 500),
    }
    for path, img in outputs.items():
        img.save(path, "PNG")
        print(f"  geschrieben: {path.relative_to(REPO_ROOT)}  {img.size} {img.mode}")
    print("Fertig. Adaptive-Icon- und Store-Assets aktualisiert.")


if __name__ == "__main__":
    main()
