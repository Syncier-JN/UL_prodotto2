import logging
from datetime import datetime
import os

# Standard-Logpfad
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ul_simulation.log")

# Stelle sicher, dass logs-Verzeichnis existiert
os.makedirs(LOG_DIR, exist_ok=True)

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # Optional: Console-Ausgabe
    ]
)

# Shortcut-Funktionen
def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)

def log_simulation_summary(user_input: dict, result_stats: dict):
    """
    Optionales Logging-Modul für zusammengefasste Simulationen.
    """
    logging.info("=== Neue Simulation ===")
    logging.info(f"Eingaben: {user_input}")
    logging.info(f"Ergebnisse: {result_stats}")
    logging.info("===")
