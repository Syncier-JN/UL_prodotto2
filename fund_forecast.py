import yfinance as yf
import pandas as pd
import numpy as np

import yfinance as yf
import pandas as pd
import numpy as np

def get_mu_sigma(fond):
    """
    Liefert (mu, sigma, letzter Kurs) für einen Fonds-Ticker oder ein Fonds-Objekt mit Ticker-Feld.
    Args:
        fond (str | dict): Ticker-String oder Dict mit 'ticker'
    Returns:
        mu (float): Erwartete jährliche Rendite
        sigma (float): Jährliche Volatilität
        S0 (float): Aktueller Kurs
    """
    if isinstance(fond, dict):
        ticker = fond.get("ticker", "")
    else:
        ticker = fond

    if not ticker:
        raise ValueError("Ticker ist leer oder ungültig.")

    data = yf.download(ticker, start="2015-01-01", end="2024-12-31", auto_adjust=True)

    if data.empty:
        raise ValueError(f"Keine Daten für Ticker {ticker} gefunden.")

    # Fehlerresistente Umwandlung
    if isinstance(data.columns, pd.MultiIndex):
        if 'Adj Close' in data.columns.get_level_values(0):
            price_series = data['Adj Close']
            if isinstance(price_series, pd.DataFrame):
                price_df = price_series.rename(columns={price_series.columns[0]: "Price"})
            else:
                price_df = price_series.to_frame(name="Price")
        else:
            price_df = data.iloc[:, 0].to_frame(name="Price")
    else:
        if 'Adj Close' in data.columns:
            price_df = data[['Adj Close']].rename(columns={'Adj Close': 'Price'})
        else:
            price_df = data.iloc[:, 0].to_frame(name="Price")

    # Renditen berechnen
    returns = np.log(price_df["Price"] / price_df["Price"].shift(1)).dropna()
    mu = returns.mean() * 252
    sigma = returns.std() * np.sqrt(252)
    S0 = price_df["Price"].iloc[-1]

    return mu, sigma, S0



def simulate_fund_path(S0, mu, sigma, days):
    """Simuliert einen einzelnen Pfad mit geometrischer brownscher Bewegung."""
    dt = 1 / 252
    prices = [S0]
    for _ in range(1, days):
        drift = (mu - 0.5 * sigma**2) * dt
        shock = sigma * np.random.normal() * np.sqrt(dt)
        price = prices[-1] * np.exp(drift + shock)
        prices.append(price)
    return prices

def simulate_multiple_paths(S0, mu, sigma, days, n_paths=100, seed=None, mode="price", contribution=None, initial_costs_pct=0.0):

    """
    Simuliert Monte-Carlo-Pfade einer geometrischen brownschen Bewegung (Fondskurs oder Portfoliowert).
    Args:

        S0 (float): Startkurs des Fonds.
        mu (float): Erwartete annualisierte Rendite.
        sigma (float): Annualisierte Volatilität.
        days (int): Anzahl Börsentage.
        n_paths (int): Anzahl Pfade.
        seed (int, optional): Seed für Reproduzierbarkeit.
        mode (str): "price" (Standard) oder "portfolio".
        contribution (float, optional): Einmalanlage für "portfolio"-Modus.
        initial_costs_pct (float): Einmalige Einstiegskosten in % (nur für "portfolio"-Modus).
    Returns:
        np.ndarray: Simulierte Pfade (Fondspreis oder Portfoliowert), shape = (days, n_paths)
    """

    if seed is not None:
        np.random.seed(seed)
    dt = 1 / 252
    drift = (mu - 0.5 * sigma**2) * dt
    shock = sigma * np.random.randn(days, n_paths) * np.sqrt(dt)
    log_returns = drift + shock
    log_paths = np.cumsum(log_returns, axis=0)
    paths = S0 * np.exp(log_paths)  # Kursverläufe
    if mode == "portfolio":
        if contribution is None:
            raise ValueError("Für 'portfolio'-Modus muss ein Beitrag angegeben werden.")
        net_contribution = contribution * (1 - initial_costs_pct / 100)
        n_shares = net_contribution / S0
        return paths * n_shares  # Portfoliowert-Verlauf
    return paths  # Kursverlauf
 

def get_historical_cagr(ticker, start="2015-01-01", end="2024-12-31"):
    data = yf.download(ticker, start=start, end=end, auto_adjust=True)
    data = data.dropna()
    if data.empty:
        raise ValueError("Keine Daten gefunden.")
    S0 = data.iloc[0]["Close"] if "Close" in data.columns else data.iloc[0, 0]
    S1 = data.iloc[-1]["Close"] if "Close" in data.columns else data.iloc[-1, 0]
    n_years = (data.index[-1] - data.index[0]).days / 365.25
    cagr = (S1 / S0) ** (1 / n_years) - 1
    return cagr
