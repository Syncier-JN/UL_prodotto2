from fund_forecast import get_mu_sigma
mu, sigma, last_price = get_mu_sigma("AOK")
print(f"mu: {mu:.4f}, sigma: {sigma:.4f}, letzter Kurs: {last_price:.2f}")