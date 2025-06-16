# app2.py
import streamlit as st
import os
import numpy as np
import pandas as pd
from ui_components import get_user_inputs_mifid
from simulation import simulate_multiple_paths, simulate_rolling_bond_process
from results_display import display_results, display_costs_summary
from mortality import load_istat_table, survival_probability
from utils import (
    days_between_ages,
    get_guarantee_cost,
    get_fonds,
    plausibility_check
)
from summary_mifid import generate_mifid_summary_pdf
from config import MIFID_FONDS
from fund_forecast import get_mu_sigma
from ui_components import plot_rolling_bond_segments

# 📄 Layout
st.set_page_config(page_title="UL Morte – MiFID Profilo", layout="wide")
st.title("📊 Simulazione basata su profilo di rischio (MiFID II)")

# 📊 Tabelle mortalità
df_mortality = load_istat_table("Tavole_di_mortalita.csv")

# 📥 Inputs
inputs = get_user_inputs_mifid()
age = int(inputs["age"])
death_age = int(inputs["death_age"])
contribution = inputs["contribution"]
mifid_class = inputs["mifid_class"]
mifid_level = int(mifid_class.split(" ")[0])
use_bond_simulation = mifid_level <= 2
st.caption(f"🧪 Profilo scelto: {mifid_class} — Classe {mifid_level} — Bond-Simulation attiva: {use_bond_simulation}")

costs_percent = inputs["costs_percent"]
n_paths = int(inputs["n_paths"])
days = int(days_between_ages(age, death_age))
T = int(death_age - age)
guarantee_levels = [0.8, 0.9, 1.0]
initial_costs_pct = 0.0

selected_guarantee = st.radio(
    "🔐 Quale livello di garanzia desideri simulare?",
    options=guarantee_levels,
    index=2,
    format_func=lambda g: f"{int(g * 100)}%"
)

pdf_path = None
total_paths_by_guarantee = {}

# ▶️ Simulazione
if inputs["ready"] and st.button("▶️ Avvia simulazione"):
    try:
        fonds = get_fonds(mifid_class)
        if not fonds:
            st.error("❌ Nessun fondo disponibile per la classe di rischio selezionata.")
            st.stop()

        fond = fonds[0]["ticker"] if isinstance(fonds[0], dict) else fonds[0]
        mu, sigma, s0 = get_mu_sigma(fond)
        sigma = sigma if sigma > 0 and not np.isnan(sigma) else 0.15

        net_contribution = contribution * (1 - initial_costs_pct / 100)
        n_shares = net_contribution / s0
        guarantee_cost_pct = get_guarantee_cost(contribution, selected_guarantee, T, sigma)

        if use_bond_simulation:
            theta = 0.2
            s0 = 1.0  # Simuliere Startzins als mu
            growth_factors = simulate_rolling_bond_process(
                s0=s0,
                mu=mu,
                theta=theta,
                sigma=sigma,
                total_days=days,
                n_paths=n_paths,
                roll_years=10
            )
            final_fund_values = growth_factors * contribution
            paths_value = np.tile(final_fund_values, (days, 1))
            end_values = final_fund_values.copy()
            asset_label = "Obbligazione (roll.)"
            st.caption(f"📌 Valore medio finale obbligazione: {np.mean(final_fund_values):,.2f} EUR")
        else:
            paths = simulate_multiple_paths(s0, mu, sigma, days, n_paths)
            paths_value = paths * n_shares
            final_fund_values = paths_value[-1, :]
            end_values = final_fund_values
            asset_label = "Fondo"

        total_annual_cost = costs_percent + guarantee_cost_pct
        if total_annual_cost > 0:
            for year in range(1, days // 252 + 1):
                idx = year * 252
                if idx < paths_value.shape[0]:
                    paths_value[idx, :] *= (1 - total_annual_cost / 100)

        guaranteed_amount = contribution * selected_guarantee
        end_values = np.maximum(end_values, guaranteed_amount)

        # 🎯 Risultati
        st.markdown(f"### 🎯 Simulazione – Garanzia {int(selected_guarantee * 100)}%")
        col1, col2, col3 = st.columns(3)
        col1.metric("💶 Capitale garantito", f"{guaranteed_amount:,.0f} EUR")
        col2.metric("📈 Media fondo (simulata)", f"{np.mean(final_fund_values):,.0f} EUR")
        col3.metric("📊 Prestazione media (finale)", f"{np.mean(end_values):,.0f} EUR")

        # 📁 Visualizzazione simulazione
        st.subheader("📁 Visualizzazione simulazione")
        if use_bond_simulation:
            plot_rolling_bond_segments(
                s0=mu, mu=mu, theta=theta, sigma=sigma,
                roll_years=10, total_years=T, n_paths=n_paths
            )
        else:
            display_results(end_values, paths_value, death_age)

        display_costs_summary(costs_percent, guarantee_cost_pct, total_annual_cost)

        for msg in plausibility_check(guaranteed_amount, np.mean(end_values), mu, sigma, label=f"Garanzia {int(selected_guarantee * 100)}%"):
            st.warning(msg)

        # 📄 PDF
        pdf_path = generate_mifid_summary_pdf(
            age, contribution, death_age, mifid_class, mu, sigma,
            costs_percent, n_paths, {selected_guarantee: paths_value}
        )
        if pdf_path:
            st.session_state["pdf_path_mifid"] = pdf_path

    except Exception as e:
        st.error(f"❌ Errore durante la simulazione: {e}")

# 📥 PDF Download
pdf_path_session = st.session_state.get("pdf_path_mifid")
if pdf_path_session and os.path.exists(pdf_path_session):
    with open(pdf_path_session, "rb") as f:
        st.download_button(
            label="📅 Scarica il PDF del confronto (MiFID)",
            data=f.read(),
            file_name="Report_MiFID.pdf",
            mime="application/pdf"
        )
elif inputs["ready"]:
    st.warning("⚠️ Premi prima 'Avvia simulazione' per generare il report.")
else:
    st.info("🔐 La simulazione richiede l'inserimento completo dei dati.")

st.markdown("ℹ️ *I risultati sono basati su simulazioni e non rappresentano una garanzia di rendimento futuro.*")
