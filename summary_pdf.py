from fpdf import FPDF
import tempfile
import numpy as np
from utils import get_guarantee_cost, price_guarantee_put
from fund_forecast import get_mu_sigma
from utils import days_between_ages

def generate_summary_pdf(age, contribution, death_age, fonds_weights, total_sigma,
                          costs_percent, n_paths, df_mortality, total_paths_by_guarantee):
    
    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.cell(0, 10, "Confronto delle prestazioni in base alla garanzia", ln=True, align="C")
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")

    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"Età di ingresso: {age} anni", ln=True)
        pdf.cell(0, 10, f"Età target (durata): {death_age} anni", ln=True)
        pdf.cell(0, 10, f"Contributo: {contribution:,.2f} EUR", ln=True)
        pdf.cell(0, 10, f"Numero simulazioni: {n_paths}", ln=True)
        pdf.cell(0, 10, f"Costi di gestione: {costs_percent:.2f}% annuo", ln=True)
        pdf.ln(5)

        # Tabelle
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(30, 10, "Garanzia", 1)
        pdf.cell(30, 10, "Media", 1)
        pdf.cell(30, 10, "Min", 1)
        pdf.cell(30, 10, "Max", 1)
        pdf.cell(30, 10, "Costo %", 1)
        pdf.cell(40, 10, "VaR (95%)", 1)
        pdf.ln()

        pdf.set_font("Helvetica", size=11)

        T = death_age - age
        days = days_between_ages(age, death_age)

        for guarantee_label, guarantee in [("80%", 0.8), ("90%", 0.9), ("100%", 1.0)]:
            K = contribution * guarantee
            put_price = price_guarantee_put(S0=contribution, K=K, T=T, sigma=total_sigma, r=0.01)
            guarantee_cost_pct = get_guarantee_cost(contribution, guarantee, T, total_sigma)
            total_annual_cost = costs_percent + guarantee_cost_pct

            paths = total_paths_by_guarantee[guarantee]

            if total_annual_cost > 0:
                for year in range(1, days // 252 + 1):
                    idx = year * 252
                    if idx < paths.shape[0]:
                        paths[idx:] *= (1 - total_annual_cost / 100)

            final_fund_values = paths[-1]
            guaranteed_amount = contribution * guarantee
            end_values = np.maximum(final_fund_values, guaranteed_amount)

            payout_mean = np.mean(end_values)
            payout_min = np.min(end_values)
            payout_max = np.max(end_values)
            var_value = np.percentile(end_values, 5)

            pdf.cell(30, 10, f"{guarantee_label}", 1)
            pdf.cell(30, 10, f"{payout_mean:,.0f} EUR", 1)
            pdf.cell(30, 10, f"{payout_min:,.0f} EUR", 1)
            pdf.cell(30, 10, f"{payout_max:,.0f} EUR", 1)
            pdf.cell(30, 10, f"{guarantee_cost_pct:.2f}%", 1)
            pdf.cell(40, 10, f"{var_value:,.0f} EUR", 1)
            pdf.ln()

        pdf.ln(5)
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(0, 8, (
            "Nota: La prestazione minima garantita incide sul costo della polizza.\n"
            "Maggiore è la garanzia, maggiore è il costo, ma anche la sicurezza per l'assicurato.\n"
            "Il Value at Risk (VaR) indica la perdita potenziale con una probabilità del 5%."
        ))

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        temp_file.close()
        return temp_file.name

    except Exception as e:
        print(f"PDF-Fehler: {e}")
        return None
