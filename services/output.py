"""
OutputService - gemeinsamer Ausgabedienst.

Kein Fachmodul, sondern Infrastruktur (wie die Datenbank). Module
erzeugen ueber diesen Dienst druckbare PDFs und Mail-Entwuerfe, ohne
selbst Drucker- oder SMTP-Logik nachzubauen. Beide Ausgaben sind
Dateien:
  - PDF  -> kann gedruckt werden
  - .eml -> kann im Mailprogramm geoeffnet und versendet werden

So bleibt die Ausgabe ein austauschbarer Kanal: spaeter koennte hier
echter SMTP-Versand oder direkter Druck ergaenzt werden, ohne dass die
Module sich aendern.
"""
from __future__ import annotations

import re
from email.message import EmailMessage
from pathlib import Path


def slugify(text: str) -> str:
    """Macht aus einem Titel einen dateinamensicheren String."""
    text = text.lower()
    text = (text.replace("ä", "ae").replace("ö", "oe")
                .replace("ü", "ue").replace("ß", "ss"))
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "dokument"


class OutputService:
    """Erzeugt Dokumente als Dateien (PDF zum Drucken, .eml fuer Mail)."""

    def __init__(self, output_dir: str = "ausgaben"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_pdf(self, title: str, body: str, filename: str) -> str:
        """Schreibt ein einfaches, druckbares PDF-Dokument."""
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(25, 25, 25)

        pdf.set_font("Helvetica", style="B", size=13)
        pdf.multi_cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

        pdf.set_font("Helvetica", size=11)
        for line in body.split("\n"):
            # leere Zeilen als Abstand, sonst Zeile setzen;
            # new_x/new_y sorgen dafuer, dass die naechste Zeile links beginnt
            pdf.multi_cell(0, 6, line if line.strip() else " ",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        path = self.output_dir / filename
        pdf.output(str(path))
        return str(path)

    def write_email_draft(self, to_addr: str, subject: str,
                          body: str, filename: str) -> str:
        """Schreibt einen Mail-Entwurf als .eml-Datei (im Mailclient oeffenbar)."""
        msg = EmailMessage()
        msg["To"] = to_addr or ""
        msg["Subject"] = subject
        msg.set_content(body)

        path = self.output_dir / filename
        path.write_bytes(bytes(msg))
        return str(path)
