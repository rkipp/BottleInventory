import polars as pl
import requests
from requests.auth import HTTPBasicAuth
from api_key import userid, apikey

# Unit conversion constants (unused in current routes but kept for reference)
OZ_PER_LITER = 1 / 33.8140227
OZ_PER_GRAM  = 1 / 0.0352739619
LBS_PER_KILO = 1 / 2.20462

# Brewfather API base URL
API_BASE = "https://api.brewfather.app/v2"


def srm_to_hex(srm):
    """Convert a beer SRM colour value to a CSS hex colour string.

    Uses an exponential decay model with different decay rates per channel
    to produce a smooth gradient from pale straw through amber to near-black.
    Returns a neutral amber fallback for missing or non-numeric input.

    Args:
        srm: numeric SRM value, or None/string if unavailable.

    Returns:
        A CSS hex colour string e.g. '#f5a623'.
    """
    try:
        srm = float(srm)
    except (TypeError, ValueError):
        return '#f5a623'

    srm = max(0, srm)
    r = int(255 * pow(0.9, srm * 0.3))
    g = int(255 * pow(0.9, srm * 0.6))
    b = int(255 * pow(0.9, srm * 1.2))
    return f'#{r:02x}{g:02x}{b:02x}'


def update_batches():
    """Fetch all batches from Brewfather and write two CSV files:

    - Data/batches.csv:    Completed and Conditioning batches.
    - Data/fermenting.csv: Fermenting and Planned batches.

    Both files include estimatedColor and measuredAbv for display purposes.
    """
    auth = HTTPBasicAuth(userid, apikey)
    url = (
        f"{API_BASE}/batches"
        "?include=measuredAbv,recipe.style,estimatedColor"
        "&limit=50&order_by=batchNo&order_by_direction=desc"
    )
    raw = pl.DataFrame(requests.get(url, auth=auth).json())

    # Shared transforms: parse brewDate and unnest recipe struct
    base = (
        raw
        .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date())
        .with_columns(pl.col('recipe').struct.unnest())
        .with_columns(beername=pl.col("name"))
        .with_columns(pl.col("style").struct.unnest())
        .with_columns(style=pl.col("name"))
        .drop("name")
        .rename({"beername": "name"})
    )

    # Completed / Conditioning batches → available for bottling
    batches = (
        base
        .filter(pl.col("status").is_in(["Completed", "Conditioning"]))
        .select(["batchNo", "brewDate", "name", "status", "measuredAbv", "style", "estimatedColor"])
        .sort('brewDate', descending=True)
    )
    batches.write_csv('./Data/batches.csv')

    # Fermenting / Planned batches → shown in the fermenter display
    fermenting = (
        raw
        .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date())
        .with_columns(pl.col('recipe').struct.unnest())
        .filter(pl.col("status").is_in(["Fermenting", "Planned"]))
        .select(["batchNo", "brewDate", "measuredAbv", "name", "status", "estimatedColor"])
        .sort('brewDate', descending=True)
    )
    fermenting.write_csv('./Data/fermenting.csv')


def get_batches():
    """Read completed/conditioning batches from CSV.

    Returns:
        Polars DataFrame. Returns a single-row placeholder if the file is empty.
    """
    batches = pl.read_csv('./Data/batches.csv')
    if batches.height == 0:
        return pl.DataFrame({"name": ["No batches found"]})
    return batches


def get_whats_fermenting():
    """Read currently fermenting/planned batches from CSV.

    Returns:
        Polars DataFrame.
    """
    return pl.read_csv('./Data/fermenting.csv')


if __name__ == "__main__":
    update_batches()
    print(get_batches())