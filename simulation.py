from fund_forecast import get_mu_sigma, simulate_multiple_paths
import numpy as np


def simulate_paths_for_all_guarantees(contribution, fonds_weights, n_paths, days, guarantee_levels):
    """
    📊 Simuliert Fondsverläufe für verschiedene Garantien (z.B. 80%, 90%, 100%).

    Returns:
        dict: guarantee_level → simulated paths (ndarray)
        dict: guarantee_level → durchschnittliche Volatilität (sigma)
    """
    total_paths_by_guarantee = {}
    sigma_by_guarantee = {}

    for guarantee in guarantee_levels:
        total_paths = None
        total_sigma = 0

        for fond, weight in fonds_weights:
            mu, sigma, s0 = get_mu_sigma(fond)
            total_sigma += sigma * (weight / 100)
            fund_contribution = contribution * (weight / 100)
            scaling_factor = fund_contribution / s0

            paths = simulate_multiple_paths(s0, mu, sigma, days, n_paths)
            paths *= scaling_factor

            if total_paths is None:
                total_paths = paths
            else:
                total_paths += paths

        sigma_by_guarantee[guarantee] = total_sigma
        total_paths_by_guarantee[guarantee] = total_paths

    return total_paths_by_guarantee, sigma_by_guarantee


def run_simulation(contribution, fonds_weights, n_paths, days, initial_costs_pct=0.0):
    """
    🧮 Simuliert die Entwicklung eines Portfolios aus Fondsanteilen.

    Returns:
        ndarray: Wertverlauf des Portfolios [days, n_paths]
        float: Durchschnittliche Volatilität (gewichtetes sigma)
    """
    total_paths = None
    total_sigma = 0
    net_contribution = contribution * (1 - initial_costs_pct / 100)

    for fond, weight in fonds_weights:
        mu, sigma, s0 = get_mu_sigma(fond)
        weight_ratio = weight / 100
        total_sigma += sigma * weight_ratio
        fund_contribution = net_contribution * weight_ratio
        n_shares = fund_contribution / s0

        paths = simulate_multiple_paths(s0, mu, sigma, days, n_paths)
        paths_value = paths * n_shares

        if total_paths is None:
            total_paths = paths_value
        else:
            total_paths += paths_value

    return total_paths, total_sigma



def simulate_ou_process(s0, mu, theta, sigma, days, n_paths, dt=1/252, seed=None):
    """
    Simuliert einen Ornstein-Uhlenbeck-Prozess.
    Liefert realistische Anleihe-Wertentwicklungen rund um den Startwert `s0`.
    """
    if seed is not None:
        np.random.seed(seed)

    steps = days
    X = np.zeros((steps + 1, n_paths))
    X[0] = s0

    for t in range(steps):
        dW = np.random.normal(0, np.sqrt(dt), size=n_paths)
        X[t + 1] = X[t] + theta * (mu - X[t]) * dt + sigma * dW

    return X  # Shape: (days+1, n_paths)

def simulate_rolling_bond_process(s0, mu, theta, sigma, total_days, n_paths, roll_years=10):
    """
    Simuliert ein rollierendes Anleiheportfolio mit Reinvestitionen alle `roll_years`.

    Gibt den Gesamt-Endwert jedes Pfades nach N Wiederanlagestufen zurück.
    """
    roll_days = int(roll_years * 252)
    n_rolls = total_days // roll_days

    value = np.ones(n_paths) * s0  # Start mit Startwert 1.0 oder s0

    for i in range(n_rolls):
        sub_path = simulate_ou_process(s0, mu, theta, sigma, days=roll_days, n_paths=n_paths)
        growth = sub_path[-1, :]  # Endwert des Teilabschnitts
        value *= growth  # Multipliziere kumulativ

    return value  # shape: (n_paths,)
