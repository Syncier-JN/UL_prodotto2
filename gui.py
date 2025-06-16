import threading
import tkinter as tk
from tkinter import ttk
from config import FONDS, GARANTIEN
from mortality import load_istat_table, simulate_death_age
from fund_forecast import get_mu_sigma, simulate_multiple_paths
from payouts import calculate_payout
from utils import days_between_ages
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Caricamento tavola di mortalità ISTAT
df_mortality = load_istat_table("Tavole_di_mortalità.csv")

# GUI setup
root = tk.Tk()
root.title("Simulazione della prestazione in caso di morte")

tk.Label(root, text="Seleziona un fondo:").pack()
fonds_combo = ttk.Combobox(root, values=list(FONDS.keys()))
fonds_combo.pack()

tk.Label(root, text="Età di ingresso:").pack()
age_entry = tk.Entry(root)
age_entry.insert(0, "65")
age_entry.pack()

tk.Label(root, text="Percentuale garantita:").pack()
guarantee_combo = ttk.Combobox(root, values=list(GARANTIEN.keys()))
guarantee_combo.set("100%")
guarantee_combo.pack()

tk.Label(root, text="Numero di simulazioni (Monte Carlo):").pack()
n_paths_var = tk.IntVar(value=100)
tk.Scale(
   root,
   from_=10,
   to=200,
   resolution=10,
   orient=tk.HORIZONTAL,
   variable=n_paths_var
).pack()

result_var = tk.StringVar()
tk.Label(root, textvariable=result_var, font=("Arial", 12)).pack(pady=5)

fig, ax = plt.subplots(figsize=(7, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

def run_simulation():
    ticker = fonds_combo.get()
    if not ticker:
        result_var.set("Seleziona un fondo.")
        return

    try:
        age = int(age_entry.get())
        if age < 0 or age > 100:
            raise ValueError
    except:
        result_var.set("Età di ingresso non valida.")
        return

    guarantee = GARANTIEN[guarantee_combo.get()]

    try:
        mu, sigma, S0 = get_mu_sigma(ticker)
    except Exception as e:
        result_var.set(f"Errore durante il caricamento dei dati del fondo: {e}")
        return

    try:
        death_age = simulate_death_age(age, df_mortality)
    except Exception as e:
        result_var.set(f"Errore nella simulazione dell'età alla morte: {e}")
        return

    days = days_between_ages(age, death_age)
    n_paths = n_paths_var.get()

    paths = simulate_multiple_paths(S0, mu, sigma, days, n_paths)
    end_values = paths[-1] * guarantee
    payout_mean = np.mean(end_values)
    payout_min = np.min(end_values)
    payout_max = np.max(end_values)

    result_var.set(
        f"Età alla morte simulata: {death_age}\n"
        f"Prestazione garantita ({int(guarantee * 100)}%):\n"
        f"Media: {payout_mean:.2f} USD | Min: {payout_min:.2f} | Max: {payout_max:.2f}"
    )

    ax.clear()
    for i in range(min(n_paths, 20)):  # Max 20 per velocità
        ax.plot(paths[:, i], alpha=0.2, linewidth=0.7)
    ax.plot(np.mean(paths, axis=1), linewidth=2, label='Media')
    ax.set_title(f"{ticker} – Simulazione Monte Carlo fino a {death_age} anni")
    ax.set_xlabel("Giorni")
    ax.set_ylabel("Valore del fondo")
    ax.legend()
    canvas.draw()

tk.Button(root, text="Avvia simulazione", command=lambda: threading.Thread(target=run_simulation).start()).pack(pady=10)


root.mainloop()
