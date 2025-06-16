import numpy as np
from scipy.stats import norm
from config import MIFID_FONDS

def days_between_ages(start_age, end_age):
    """Berechnet die Anzahl an Börsentagen zwischen zwei Alterswerten."""
    years = end_age - start_age
    return years * 252  # 252 Börsentage pro Jahr

def get_guarantee_cost(contribution, guarantee_level, T, sigma, r=0.01):
    """
    Dynamische Garantiekostenberechnung auf Basis Black-Scholes (jährlicher %-Wert).
    """
    K = contribution * guarantee_level
    put_price = price_guarantee_put(S0=contribution, K=K, T=T, sigma=sigma, r=r)
    annual_pct = (put_price / contribution) * (1 / T) * 100
    return annual_pct


def price_guarantee_put(S0, K, T, sigma, r=0.01):
    """
    Berechnet den Preis einer europäischen Put-Option nach Black-Scholes,
    zur Bewertung einer Beitragsgarantie bei Todesfall.

    Parameter:
        S0     – Aktueller Fondswert (EUR)
        K      – Garantiebetrag (EUR)
        T      – Laufzeit bis Todesfall (in Jahren)
        sigma  – Volatilität (annualisiert)
        r      – risikofreier Zinssatz (standard: 1%)

    Rückgabe:
        Preis der Garantieoption (in EUR)
    """
    if T <= 0 or sigma <= 0:
        return max(K - S0, 0)

    d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)
    return max(put_price, 0)

def apply_annual_costs(paths, total_annual_cost, days):
    """
    Wendet jährliche Kosten auf die simulierten Pfade an (nur an Jahrestagen).
    """
    if total_annual_cost > 0:
        for year in range(1, days // 252 + 1):
            idx = year * 252
            if idx < paths.shape[0]:
                paths[idx:] *= (1 - total_annual_cost / 100)
    return paths

def days_between_ages(start_age, end_age):
    return int((end_age - start_age) * 252)

def is_mifid_fund_valid(mifid_class, mu, sigma):
   if mifid_class.startswith("1") and (mu < 0 or sigma > 0.05):
       return False
   if mifid_class.startswith("2") and sigma > 0.10:
       return False
   if mifid_class.startswith("3") and sigma > 0.20:
       return False
   return True

def get_fonds(mifid_class):
    """
    Gibt die passende Fonds-Liste zur MiFID-Klasse zurück.
    Akzeptiert Klassen wie '1', '1 - Prudente', '3 - Bilanciato' usw.
    """
    if not mifid_class:
        return []

    key = str(mifid_class).strip().split()[0]  # nur Zahl extrahieren
    return MIFID_FONDS.get(key, [])

def plausibility_check(guaranteed_amount, mean_final, mu, sigma, label=""):
    warnings = []
    ratio = mean_final / guaranteed_amount if guaranteed_amount > 0 else 0

    if mean_final <= guaranteed_amount:
        warnings.append(
            f"⚠️ {label}: La prestazione media ({mean_final:,.0f} EUR) ≤ capitale garantito ({guaranteed_amount:,.0f} EUR)."
        )
    if ratio > 3:
        warnings.append(
            f"❗ {label}: Rapporto media/garanzia molto alto ({ratio:.1f}). μ={mu:.2%}, σ={sigma:.2%}."
        )
    if mu < 0 and mean_final > guaranteed_amount:
        warnings.append(
            f"❓ {label}: μ negativo ma risultato medio positivo ({mean_final:,.0f} EUR)."
        )
    if sigma < 0.05 and ratio > 1.5:
        warnings.append(
            f"❗ {label}: Volatilità bassa (σ={sigma:.2%}) ma risultato alto."
        )
    return warnings

