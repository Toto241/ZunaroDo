"""
PDF-Reports auf Basis der Statistik-Aggregate.

Nutzt fpdf2 (ohnehin Pflicht-Abhaengigkeit fuer Kuendigungsschreiben).
Eine schlichte, druckbare A4-Seite mit Jahresueberblick - kein Diagramm,
sondern Tabellen.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional


def make_yearly_report(target: Path, year: int,
                        yearly: dict,
                        contracts: dict,
                        per_category: dict) -> Path:
    """
    Schreibt einen PDF-Jahresbericht.

    'yearly'        ist die Antwort von stats.yearly_summary
    'contracts'     ist die Antwort von stats.contracts_overview
    'per_category'  ist die Antwort von stats.expenses_per_category
    """
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    target.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # Titel
    pdf.set_font("Helvetica", style="B", size=18)
    pdf.cell(0, 12, f"ZunaroDo - Jahresbericht {year}",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font("Helvetica", style="I", size=9)
    pdf.cell(0, 6,
              f"Erstellt am {date.today().strftime('%d.%m.%Y')}",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Ausgaben
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 8, "Ausgaben",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6,
              f"  Posten gesamt:           {yearly['expense_count']}",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6,
              f"  Summe ueber das Jahr:    {yearly['expense_total']:.2f} EUR",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6,
              f"  Durchschnitt pro Monat:  {yearly['average_per_month']:.2f} EUR "
              f"(ueber {yearly['elapsed_months']} Monate)",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Top-Kategorien
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 7, "Top-Kategorien",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    top_cats = yearly.get("top_categories", [])
    if not top_cats:
        pdf.cell(0, 6, "  (keine Ausgaben in diesem Jahr)",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for entry in top_cats:
        pdf.cell(0, 6,
                  f"  {entry['category']:18s}  {entry['total']:>10.2f} EUR",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Vertraege
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 8, "Vertraege",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6,
              f"  Aktive Vertraege:        {contracts['count']}",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6,
              f"  Monatliche Belastung:    {contracts['monthly_total']:.2f} EUR",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6,
              f"  Jaehrliche Hochrechnung: {contracts['yearly_total']:.2f} EUR",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.cell(0, 7, "Top 3 Kostentreiber",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=10)
    for entry in contracts.get("top_3", []):
        pdf.cell(0, 6,
                  f"  {entry['name']:24s}  {entry['monthly_cost']:>7.2f} EUR/Monat",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Fusszeile
    pdf.ln(10)
    pdf.set_font("Helvetica", style="I", size=8)
    pdf.cell(0, 6,
              "Dieses Dokument wurde lokal von ZunaroDo "
              "erzeugt - keine Cloud-Uebertragung.",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(target))
    return target
