import polars as pl
import requests
from requests.auth import HTTPBasicAuth
from api_key import userid, apikey

import math

def srm_to_hex(srm):
    """Convert SRM beer color value to a hex color string.
    Uses exponential decay formula, handles decimals and high SRM values.
    """
    if srm is None or str(srm).strip() in ("", "None", "nan"):
        return "#f5a623"  # default amber
    try:
        srm = max(0, float(srm))
    except (ValueError, TypeError):
        return "#f5a623"
    r = min(255, round(255 * math.exp(-0.0089 * srm)))
    g = min(255, round(255 * math.exp(-0.0647 * srm)))
    b = min(255, round(255 * math.exp(-0.1958 * srm)))
    return f"#{r:02x}{g:02x}{b:02x}"

# Constants
oz_p_liter = (1/33.8140227)
oz_p_gram  = (1/0.0352739619)
lbs_p_kilo = (1/2.20462)

def update_batches():
    auth = HTTPBasicAuth(userid, apikey)
    raw_batches = pl.DataFrame(requests.get('https://api.brewfather.app/v2/batches?include=measuredAbv,estimatedColor,recipe.style&limit=50&order_by=batchNo&order_by_direction=desc', auth=auth).json())

    batches = (raw_batches
               .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date(), pl.col('recipe').struct.unnest())
               .with_columns(beername=pl.col("name"))
               .with_columns(pl.col("style").struct.unnest())
               .with_columns(style=pl.col("name"))
               .drop("name")
               .filter(pl.col("status").is_in(["Completed", "Conditioning"]))
               .rename({"beername":"name"})
               .select(["batchNo", "brewDate", "name", "status", "measuredAbv", "style", "estimatedColor"])
               .sort('brewDate', descending=True))
    batches.write_csv('./Data/batches.csv')
    fermenting = (raw_batches
               .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date(), pl.col('recipe').struct.unnest())
               .filter(pl.col("status").is_in(["Fermenting", "Planned",]))
               .select(["batchNo","brewDate","measuredAbv","name","status","estimatedColor"])
               .sort('brewDate', descending=True))
    
    fermenting.write_csv('./Data/fermenting.csv')


def get_whats_fermenting():
    batches = pl.read_csv('./Data/fermenting.csv')
    return batches
    

def get_batches():
    batches = pl.read_csv('./Data/batches.csv')
    if batches.height == 0:
        batches = pl.DataFrame({"name": ["No batches found"]})
    return batches

if __name__ == "__main__":
    update_batches()
    print(get_batches())