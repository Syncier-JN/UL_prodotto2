import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def display_results(end_values, total_paths, death_age):
    st.markdown(
        f"### 📈 Prestazione in caso di morte (valore finale massimo)\n"
        f"- **Media:** {np.mean(end_values):,.2f} €\n"
        f"- **Minimo:** {np.min(end_values):,.2f} €\n"
        f"- **Massimo:** {np.max(end_values):,.2f} €"
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    for i in range(min(total_paths.shape[1], 20)):
        ax.plot(total_paths[:, i], alpha=0.2, linewidth=0.7)
    ax.plot(np.mean(total_paths, axis=1), linewidth=2, label='Media')
    ax.set_title(f"Portafoglio – Simulazione Monte Carlo fino a {death_age} anni")
    ax.set_xlabel("Giorni")
    ax.set_ylabel("Valore del portafoglio")
    ax.legend()
    st.pyplot(fig)

def display_costs_summary(costs_percent, guarantee_cost_pct, total_annual_cost):
    with st.expander("🌐 Dettagli sui costi annuali stimati"):
        st.markdown(
            f"- **Costi di gestione:** {costs_percent:.2f}% annuo\n"
            f"- **Costo della garanzia (Black-Scholes):** {guarantee_cost_pct:.2f}% annuo\n"
            f"- **Totale stimato:** {total_annual_cost:.2f}% annuo"
        )
