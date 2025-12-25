import requests
from datetime import date
import streamlit as st

FX_API_URL = "https://api.exchangerate.host/latest"

def fetch_fx_rates(base_currency, currencies):
    """
    Fetch FX rates with base_currency as reference.
    """
    

    symbols = ",".join([c for c in currencies if c != base_currency])
    if not symbols:
        return {}

    params = {
        "base": base_currency,
        "symbols": symbols
    }

    response = requests.get(FX_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    rates = data.get("rates", {})

    # Always inject base currency explicitly
    rates[base_currency] = 1.0

    return rates

def get_fx_rates_cached(base_currency, currencies):
    fx = fetch_fx_rates(base_currency, currencies)

    rates = {}
    for cur in currencies:
        if cur == base_currency:
            rates[cur] = 1.0
        else:
            # If API misses a currency → fallback to 1.0
            rates[cur] = fx.get(cur) or 1.0

    return rates

