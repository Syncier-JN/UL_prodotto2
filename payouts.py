# payouts.py

def calculate_payout(fund_path, guarantee_factor):
    """Berechnet die Auszahlung am Ende des Pfads unter Berücksichtigung der Garantie."""
    final_value = fund_path[-1]
    return final_value * guarantee_factor
