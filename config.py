# config.py
FONDS = {
   "MACFX": "MFS Conservative Allocation Fund",
   "AOK": "iShares Core 30/70 ETF",
   "OICAX": "JPM Conservative Growth A",
   "MCKKX": "MainStay Conservative Allocation Fund",
   "FTCIX": "Franklin Conservative Allocation"
}
GARANTIEN = {
   "100%": 1.0,
   "90%": 0.9,
   "80%": 0.8
}
# Mapping: Risikoklasse → Liste von Fonds-Tickern
MIFID_FONDS = {
    "1": [  # Prudente (nur Bonds / kurzlaufend)
        {
            "name": "iShares 1-3 Year Treasury Bond ETF",
            "isin": "US4642874576",
            "ticker": "SHY"
        },
        {
            "name": "Lyxor Euro Government Bond 1–3Y UCITS ETF",
            "isin": "LU1598698815",
            "ticker": "EG13.DE"
        }
    ],
    "2": [  # Moderato (etwas breiteres Bond-Universum)
        {
            "name": "iShares Euro Aggregate Bond 1–5y",
            "isin": "IE00B1FZS913",
            "ticker": "EUNA.DE"
        },
        {
            "name": "Xtrackers II EUR Corporate Bond UCITS ETF",
            "isin": "LU0478205379",
            "ticker": "XBLC.DE"
        }
    ],
    "3": [  # Bilanciato (50/50 ETF)
        "IWDA.AS",       # MSCI World
        "VLS40.L"        # Vanguard LifeStrategy 40%
    ],
    "4": [              # Dinamico
        "848182.DE"      # Allianz Wachstum Europa
    ],
    "5": [              # Aggressivo
        "DWS0QF.DE"      # DWS Global Emerging Markets
    ]
}
