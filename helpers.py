# helpers.py
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


def apply_costs(paths, annual_costs_pct, days):
    """Reduziert alle Pfade jährlich um die angegebenen Kosten."""
    if annual_costs_pct > 0:
        for year in range(1, int(days) // 252 + 1):
            idx = year * 252
            if idx < paths.shape[0]:
                paths[idx:] *= (1 - annual_costs_pct / 100)
    return paths


def apply_guarantee(paths, contribution, guarantee_level):
    """Ersetzt den letzten Wert eines jeden Pfades durch max(Garantie, Fonds)."""
    guaranteed_amount = contribution * guarantee_level
    paths[-1] = np.maximum(paths[-1], guaranteed_amount)
    return paths


def plot_paths(paths, death_age, guarantee_level=None):
    """Zeichnet die simulierten Pfade."""
    fig, ax = plt.subplots(figsize=(8, 4))
    for i in range(min(paths.shape[1], 20)):
        ax.plot(paths[:, i], alpha=0.2, linewidth=0.8)
    ax.plot(np.mean(paths, axis=1), color="black", linewidth=2, label="Media")
    if guarantee_level is not None:
        ax.axhline(paths[-1].min(), color="red", linestyle="--", label="Garanzia minima")
    ax.set_title(f"Simulazione Monte Carlo – Età finale: {death_age} anni")
    ax.set_xlabel("Giorni")
    ax.set_ylabel("Valore del fondo")
    ax.legend()
    st.pyplot(fig)
