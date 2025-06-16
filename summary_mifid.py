from fpdf import FPDF
import numpy as np
import datetime
import os
from utils import get_guarantee_cost, price_guarantee_put, days_between_ages, plausibility_check

def sanitize_text_for_pdf(text):
    if not isinstance(text, str):
        text = str(text)
    return text.encode("latin-1", "ignore").decode("latin-1")

class StyledPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Confronto delle prestazioni (profilo MiFID)", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")

def generate_mifid_summary_pdf(age, contribution, death_age, mifid_class, mu, sigma, costs_percent, n_paths, total_paths_by_guarantee):
    pdf = StyledPDF()
    pdf.add_page()

    pastel_colors = {
        0.8: (230, 242, 255),  # Light Blue
        0.9: (232, 248, 245),  # Light Green
        1.0: (255, 249, 230),  # Light Yellow
    }

    pdf.set_font("Helvetica", "", 12)
    entries = [
        f"Età: {age} anni",
        f"Età alla morte simulata: {death_age} anni",
        f"Contributo iniziale: {contribution:,.2f} EUR",
        f"Classe di rischio: {mifid_class}",
        f"Rendimento atteso: {mu * 100:.2f} %",
        f"Volatilità stimata: {sigma * 100:.2f} %",
        f"Costi annuali complessivi: {costs_percent:.2f} %",
        f"Numero simulazioni Monte Carlo: {n_paths}"
    ]
    for line in entries:
        pdf.cell(0, 10, sanitize_text_for_pdf(line), ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, sanitize_text_for_pdf("Risultati per livello di garanzia:"), ln=True)
    pdf.ln(3)

    all_warnings = []

    for guarantee, paths in total_paths_by_guarantee.items():
        r, g, b = pastel_colors.get(guarantee, (245, 245, 245))
        pdf.set_fill_color(r, g, b)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, sanitize_text_for_pdf(f"Garanzia {int(guarantee * 100)}%"), ln=True, fill=True)

        final_values = paths[-1, :]
        guaranteed_amount = contribution * guarantee
        end_values = np.maximum(final_values, guaranteed_amount)

        mean = np.mean(end_values)
        min_ = np.min(end_values)
        max_ = np.max(end_values)
        var_5 = np.percentile(end_values, 5)
        cvar = np.mean(end_values[end_values <= var_5])

        pdf.set_font("Helvetica", "", 11)
        details = [
            f"- Capitale garantito: {guaranteed_amount:,.2f} EUR",
            f"- Prestazione media simulata: {mean:,.2f} EUR",
            f"- Minimo / Massimo: {min_:,.2f} EUR / {max_:,.2f} EUR",
            f"- VaR 95%: {var_5:,.2f} EUR",
            f"- CVaR (media sotto 5%): {cvar:,.2f} EUR"
        ]
        for line in details:
            pdf.cell(0, 8, sanitize_text_for_pdf(line), ln=True)
        pdf.ln(2)

        # Plausibilitätsprüfung sammeln
        warnings = plausibility_check(guaranteed_amount, mean, mu, sigma, label=f"Garanzia {int(guarantee * 100)}%")
        all_warnings.extend(warnings)

    # Hinweisbox für Plausibilitätsprüfungen
    if all_warnings:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Nota di verifica (Plausibilità):", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for warn in all_warnings:
            pdf.multi_cell(0, 8, sanitize_text_for_pdf(warn))

    folder = "pdf_output"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(folder, f"mifid_simulation_{timestamp}.pdf")
    pdf.output(file_path)
    return file_path
