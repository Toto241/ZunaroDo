"""
OutputService - gemeinsamer Ausgabedienst.

Kein Fachmodul, sondern Infrastruktur. Module erzeugen ueber diesen
Dienst Dokumente, ohne selbst Drucker- oder SMTP-Logik nachzubauen.

Kanaele:
  - write_pdf()           - PDF-Datei im Ausgabeordner
  - write_email_draft()   - .eml-Datei zum Oeffnen im Mailclient
  - print_file()          - schickt eine Datei an den Standard-Drucker
                            (OS-spezifisch; Windows via os.startfile)
  - send_smtp()           - sendet die Mail wirklich, sofern SMTP-Konfig
                            angegeben wurde (sonst Hinweis, keine Fehler)

So bleibt die Ausgabe ein austauschbarer Kanal.
"""
from __future__ import annotations

import os
import re
import smtplib
import subprocess
import sys
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Optional


def slugify(text: str) -> str:
    text = text.lower()
    text = (text.replace("ä", "ae").replace("ö", "oe")
                .replace("ü", "ue").replace("ß", "ss"))
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "dokument"


@dataclass
class SmtpConfig:
    """Konfiguration fuer echten Mailversand (optional)."""
    host: str
    port: int = 587
    username: str = ""
    password: str = ""
    sender: str = ""
    use_starttls: bool = True


class OutputService:
    """Erzeugt Dokumente und gibt sie an Druck/Mail weiter."""

    def __init__(self, output_dir: str = "ausgaben",
                 smtp: Optional[SmtpConfig] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.smtp = smtp

    # ---- PDF -----------------------------------------------------------
    def write_pdf(self, title: str, body: str, filename: str) -> str:
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
            pdf.multi_cell(0, 6, line if line.strip() else " ",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        path = self.output_dir / filename
        pdf.output(str(path))
        return str(path)

    # ---- Mail (Entwurf + echter Versand) -------------------------------
    def write_email_draft(self, to_addr: str, subject: str,
                          body: str, filename: str) -> str:
        msg = EmailMessage()
        msg["To"] = to_addr or ""
        msg["Subject"] = subject
        msg.set_content(body)
        path = self.output_dir / filename
        path.write_bytes(bytes(msg))
        return str(path)

    def send_smtp(self, to_addr: str, subject: str, body: str) -> dict:
        """Echter Versand ueber SMTP. Ohne Konfig: klarer Hinweis."""
        if self.smtp is None:
            return {"status": "uebersprungen",
                    "hinweis": ("Kein SMTP konfiguriert - "
                                 "OutputService(smtp=SmtpConfig(...)) setzen.")}
        msg = EmailMessage()
        msg["From"] = self.smtp.sender or self.smtp.username
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.smtp.host, self.smtp.port, timeout=15) as s:
                if self.smtp.use_starttls:
                    s.starttls()
                if self.smtp.username:
                    s.login(self.smtp.username, self.smtp.password)
                s.send_message(msg)
        except Exception as exc:
            return {"status": "fehler", "error": str(exc)}
        return {"status": "gesendet", "to": to_addr}

    # ---- Drucken -------------------------------------------------------
    @staticmethod
    def print_file(path: str) -> dict:
        """
        Schickt die Datei an den Standard-Drucker. OS-spezifisch.

        Unter Unix laeuft das ueber subprocess.run mit Argument-Liste
        (kein Shell) - so spielen Pfade mit Leerzeichen, Anfuehrungs-
        zeichen oder anderen Sonderzeichen keine Rolle.
        """
        if not Path(path).exists():
            return {"status": "fehler", "error": f"Datei '{path}' fehlt"}
        try:
            if sys.platform.startswith("win"):
                os.startfile(path, "print")             # type: ignore[attr-defined]
            else:
                cmd = "lpr" if sys.platform == "darwin" else "lp"
                result = subprocess.run(
                    [cmd, path], check=False, capture_output=True,
                    text=True)
                if result.returncode != 0:
                    return {"status": "fehler",
                            "error": (result.stderr.strip()
                                       or f"{cmd} -> Exit {result.returncode}")}
        except FileNotFoundError:
            return {"status": "fehler",
                    "error": "Drucker-Hilfsprogramm 'lp'/'lpr' nicht gefunden"}
        except Exception as exc:                        # pragma: no cover
            return {"status": "fehler", "error": str(exc)}
        return {"status": "an Drucker geschickt", "path": path}
