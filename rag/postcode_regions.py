# Coarse UK postcode-area → region mapping. Heuristic, not precise geocoding —
# good enough to give the embedding model an explicit geographic signal instead
# of an opaque postcode string it can't reliably interpret.
import pandas as pd
NATION_MAP = {
    "AB": "Scotland", "DD": "Scotland", "DG": "Scotland", "EH": "Scotland",
    "FK": "Scotland", "G": "Scotland", "HS": "Scotland", "IV": "Scotland",
    "KA": "Scotland", "KW": "Scotland", "KY": "Scotland", "ML": "Scotland",
    "PA": "Scotland", "PH": "Scotland", "TD": "Scotland", "ZE": "Scotland",
    "CF": "Wales", "LD": "Wales", "LL": "Wales", "NP": "Wales", "SA": "Wales",
    "BT": "Northern Ireland",
}

ENGLAND_REGION_MAP = {
    "NE": "North East England", "SR": "North East England", "DH": "North East England",
    "DL": "North East England", "TS": "North East England",
    "CA": "North West England", "LA": "North West England", "FY": "North West England",
    "PR": "North West England", "BB": "North West England", "BL": "North West England",
    "WN": "North West England", "L": "North West England", "WA": "North West England",
    "CH": "North West England", "M": "North West England", "OL": "North West England", "SK": "North West England",
    "LS": "Yorkshire", "BD": "Yorkshire", "HD": "Yorkshire", "HX": "Yorkshire",
    "WF": "Yorkshire", "YO": "Yorkshire", "HG": "Yorkshire", "DN": "Yorkshire", "S": "Yorkshire", "HU": "Yorkshire",
    "B": "Midlands", "CV": "Midlands", "DY": "Midlands", "WS": "Midlands", "WV": "Midlands",
    "TF": "Midlands", "ST": "Midlands", "DE": "Midlands", "NG": "Midlands", "LE": "Midlands",
    "NN": "Midlands", "PE": "Midlands", "LN": "Midlands", "WR": "Midlands", "HR": "Midlands", "SY": "Midlands",
    "E": "London", "EC": "London", "N": "London", "NW": "London", "SE": "London",
    "SW": "London", "W": "London", "WC": "London",
    "BN": "South East England", "GU": "South East England", "ME": "South East England",
    "MK": "South East England", "OX": "South East England", "RG": "South East England",
    "SL": "South East England", "SO": "South East England", "TN": "South East England",
    "PO": "South East England", "RH": "South East England", "CT": "South East England",
    "BR": "South East England", "CR": "South East England", "DA": "South East England",
    "EN": "South East England", "HA": "South East England", "IG": "South East England",
    "KT": "South East England", "RM": "South East England", "SM": "South East England",
    "TW": "South East England", "UB": "South East England", "WD": "South East England",
    "SG": "South East England", "LU": "South East England", "AL": "South East England",
    "SS": "South East England", "CM": "South East England", "CO": "South East England",
    "IP": "East England", "NR": "East England", "CB": "East England",
    "BA": "South West England", "BS": "South West England", "BH": "South West England",
    "DT": "South West England", "EX": "South West England", "GL": "South West England",
    "PL": "South West England", "SN": "South West England", "SP": "South West England",
    "TA": "South West England", "TQ": "South West England", "TR": "South West England",
}


def region_for_postcode(postcode) -> str:
    """Map a UK postcode to a coarse region name. Handles missing/null values
    explicitly — pandas represents a missing CSV field as NaN (a float), not
    an empty string, so a naive .strip() call on it would raise AttributeError."""
    if postcode is None or (isinstance(postcode, float) and pd.isna(postcode)):
        return "United Kingdom"

    postcode = str(postcode)

    area = ""
    for ch in postcode.strip():
        if ch.isalpha():
            area += ch
        else:
            break
    area = area.upper()

    if area in NATION_MAP:
        return NATION_MAP[area]
    if area in ENGLAND_REGION_MAP:
        return f"{ENGLAND_REGION_MAP[area]}, England"
    return "United Kingdom"
