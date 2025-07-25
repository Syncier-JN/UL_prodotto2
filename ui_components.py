import streamlit as st
from config import FONDS, GARANTIEN
import matplotlib.pyplot as plt
import numpy as np
from simulation import simulate_ou_process
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# Standard-Konfiguration (für app.py)
def get_user_inputs():
    st.sidebar.header("📋 Parametri del contratto")

    age = st.sidebar.number_input("Età di ingresso", min_value=18, max_value=100, value=38)
    death_age = st.sidebar.number_input("Età target (durata del contratto)", min_value=age + 1, max_value=120, value=90)
    contribution = st.sidebar.number_input("Contributo unico (EUR)", min_value=250, max_value=500_000, step=250, value=10_000)
    guarantee_label = st.sidebar.selectbox("Garanzia (%)", list(GARANTIEN.keys()))
    guarantee = GARANTIEN[guarantee_label]

    st.sidebar.markdown("---")
    costs_percent = st.sidebar.slider("Costi annuali di gestione (%)", 0.0, 5.0, 1.0, step=0.1)
    n_paths = st.sidebar.slider("Numero simulazioni (Monte Carlo)", 10, 200, 100, step=10)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Allocazione del fondo (max 5 fondi)")

    fonds_weights = []
    available_fonds = list(FONDS.keys())
    total_weight = 0

    for i in range(5):
        fond = st.sidebar.selectbox(f"Fondo {i + 1}", ["-"] + available_fonds, key=f"fond_{i}") 
        weight = st.sidebar.number_input(f"% Fondo {i + 1}", min_value=0, max_value=100, step=5, value=0, key=f"weight_{i}")
        if fond != "-":
            fonds_weights.append((fond, weight))
            total_weight += weight

    ready = total_weight == 100
    if not ready:
        st.sidebar.warning("⚠️ La somma delle allocazioni deve essere 100%.")

    return {
        "age": age,
        "death_age": death_age,
        "contribution": contribution,
        "guarantee_label": guarantee_label,
        "guarantee": guarantee,
        "fonds_weights": fonds_weights,
        "costs_percent": costs_percent,
        "n_paths": n_paths,
        "ready": ready
    }

# Alternative Konfiguration (für app2.py – MiFID II Profil)
def get_user_inputs_mifid():
    st.subheader("🔧 Parametri contratto (profilo rischio MiFID)")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Età di ingresso", min_value=18, max_value=100, value=38)
        contribution = st.number_input("Contributo unico (EUR)", 250, 500_000, step=250, value=10_000)

    with col2:
        death_age = st.number_input("Età target (durata contratto)", min_value=age + 1, max_value=120, value=85)
        costs_percent = st.slider("Costi annuali (%)", 0.0, 5.0, 1.0, step=0.1)

    st.subheader("🧠 Profilo di rischio (MiFID II)")
    mifid_class = st.selectbox(
        "Seleziona il profilo:",
        ["1 - Prudente", "2 - Moderato", "3 - Bilanciato", "4 - Dinamico", "5 - Aggressivo"]
    )

    mifid_parameters = {
        "1 - Prudente":     {"mu": 0.02, "sigma": 0.05},
        "2 - Moderato":     {"mu": 0.03, "sigma": 0.08},
        "3 - Bilanciato":   {"mu": 0.04, "sigma": 0.12},
        "4 - Dinamico":     {"mu": 0.05, "sigma": 0.18},
        "5 - Aggressivo":   {"mu": 0.06, "sigma": 0.25}
    }

    params = mifid_parameters[mifid_class]
    n_paths = st.slider("Numero di simulazioni (Monte Carlo)", 10, 200, 100, step=10)
    ready = True if contribution > 0 else False

    return {
        "age": age,
        "death_age": death_age,
        "contribution": contribution,
        "mifid_class": mifid_class,
        "mifid_level": int(mifid_class.split(" ")[0]),  # optional
        "mu": params["mu"],
        "sigma": params["sigma"],
        "costs_percent": costs_percent,
        "n_paths": n_paths,
        "ready": ready
    }

def simulate_rolling_bond_process(s0, mu, theta, sigma, total_days, n_paths, roll_years=10):
    roll_days = int(roll_years * 252)
    n_rolls = total_days // roll_days
    value = np.ones(n_paths)

    for _ in range(n_rolls):
        sub_path = simulate_ou_process(
            s0=s0, mu=mu, theta=theta, sigma=sigma,
            days=roll_days, n_paths=n_paths
        )
        r = np.clip(np.mean(sub_path, axis=0), 0, None)
        growth = (1 + r) ** roll_years
        value *= growth

    return value

def plot_rolling_bond_segments(s0, mu, theta, sigma, roll_years, total_years, n_paths):
    """
    Visualizzazione maklerfreundlich: Valori medi in EUR simulati per obbligazioni reinvestite.
    """
    if total_years < roll_years:
        st.info(f"📭 Durata ({total_years} anni) troppo breve per segmenti da {roll_years} anni.")
        return

    roll_days = int(roll_years * 252)
    n_rolls = total_years // roll_years
    results = []

    for i in range(n_rolls):
        sub_path = simulate_ou_process(
            s0=s0,
            mu=mu,
            theta=theta,
            sigma=sigma,
            days=roll_days,
            n_paths=n_paths
        )
        end_yield = np.clip(sub_path[-1, :], 0, None)
        bond_growth = (1 + end_yield) ** roll_years
        avg_val_eur = np.mean(bond_growth) * 1000  # auf 1.000 EUR Startwert bezogen

        results.append({
            "Periodo": f"{i * roll_years + 1}-{(i + 1) * roll_years}",
            "Valore medio (EUR)": avg_val_eur
        })

    df = pd.DataFrame(results)

    fig = px.bar(
        df,
        x="Periodo",
        y="Valore medio (EUR)",
        text_auto=".0f",
        color="Valore medio (EUR)",
        color_continuous_scale="Blues",
        title="📊 Crescita media dell'investimento obbligazionario per segmento"
    )
    fig.update_layout(
        yaxis_title="Valore medio simulato (su 1.000 EUR investiti)",
        xaxis_title="Periodo (anni)",
        plot_bgcolor="#fafafa",
        bargap=0.25,
        font=dict(size=14)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("ℹ️ Ogni barra rappresenta il valore medio simulato di un'obbligazione zero-coupon reinvestita ogni 10 anni, su base 1.000 EUR.")
def plot_bond_growth_over_time(s0, mu, theta, sigma, total_years, n_paths, roll_years=10, initial_investment=10_000):
    """
    Zeigt die simulierte Entwicklung eines rollierenden Anleiheinvestments über die Zeit.
    """
    roll_days = int(roll_years * 252)
    n_rolls = total_years // roll_years
    time_points = [i * roll_years for i in range(n_rolls + 1)]
    values = np.ones((n_paths,)) * initial_investment
    avg_growth = [initial_investment]

    for _ in range(n_rolls):
        rates = simulate_ou_process(s0=s0, mu=mu, theta=theta, sigma=sigma, days=roll_days, n_paths=n_paths)
        end_yield = np.clip(rates[-1, :], 0, None)
        bond_growth = (1 + end_yield) ** roll_years
        values *= bond_growth
        avg_growth.append(np.mean(values))

    df = pd.DataFrame({
        "Anno": time_points,
        "Valore medio stimato (€)": avg_growth
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Anno"],
        y=df["Valore medio stimato (€)"],
        mode="lines+markers",
        name="Valore medio",
        line=dict(width=4, color="steelblue"),
        marker=dict(size=8, symbol="circle", color="steelblue")
    ))

    fig.update_layout(
        title="📈 Crescita stimata dell’investimento obbligazionario (roll.)",
        xaxis_title="Anni trascorsi",
        yaxis_title="Valore medio (€)",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(size=16),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_yaxes(tickprefix="€", separatethousands=True)

    st.plotly_chart(fig, use_container_width=True)