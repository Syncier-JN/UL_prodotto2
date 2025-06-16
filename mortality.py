import pandas as pd
import numpy as np

def load_istat_table(path='Tavole_di_mortalità.csv'):
    df = pd.read_csv(path)
    df = df[['Età', 'qx']].dropna()

    if df['qx'].max() > 1:
        df['qx'] /= 100

    df['cum_qx'] = df['qx'].cumsum()
    df['cum_qx'] /= df['cum_qx'].iloc[-1]
    return df

def simulate_death_age(current_age, df):
    r = np.random.rand()
    filtered = df[df['Età'] >= current_age]
    match = filtered[filtered['cum_qx'] >= r]
    if not match.empty:
        return int(match['Età'].iloc[0])
    return int(filtered['Età'].max())

def get_qx_safe(df, age):
    row = df.loc[df['Età'] == age, 'qx']
    if not row.empty:
        return float(row.values[0])
    return 0.0  # Fallback

def survival_probability(start_age, death_age, df):
    """Berechnet die Überlebenswahrscheinlichkeit vom Startalter bis zum Zielalter."""
    probs = []
    for age in range(int(start_age), int(death_age)):
        row = df.loc[df['Età'] == age, 'qx']
        if row.empty:
            print(f"⚠️ Kein qx-Wert gefunden für Alter {age}")
            continue
        qx = row.values[0]
        qx = min(max(qx, 0.0), 1.0)
        probs.append(1 - qx)
    if not probs:
        return 0.0
    return float(np.prod(probs))


def quantile_death_age(start_age, df, quantile=0.95):
    cumulative = 0.0
    for age in range(int(start_age) + 1, 121):
        qx = get_qx_safe(df, age)
        cumulative += qx * (1 - cumulative)
        if cumulative >= quantile:
            return age
    return 120

def age_at_survival_probability(start_age, df, target_prob=0.95):
    survival = 1.0
    for age in range(int(start_age) + 1, 121):
        qx = get_qx_safe(df, age)
        survival *= (1 - qx)
        if survival <= (1 - target_prob):
            return age
    return 120

# Testlauf
if __name__ == "__main__":
    df = load_istat_table()
    print(df.head())
    print("Simuliertes Sterbealter:", simulate_death_age(65, df))
    print("Überlebenswahrscheinlichkeit bis 85:", survival_probability(65, 85, df))
