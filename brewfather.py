import polars as pl
import requests
from requests.auth import HTTPBasicAuth
from api_key import userid, apikey

# Constants
oz_p_liter = (1/33.8140227)
oz_p_gram  = (1/0.0352739619)
lbs_p_kilo = (1/2.20462)

def update_batches():
    auth = HTTPBasicAuth(userid, apikey)
    raw_batches = pl.DataFrame(requests.get('https://api.brewfather.app/v2/batches?limit=50&order_by=batchNo', auth=auth).json())
    
    batches = (raw_batches
               .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date(), pl.col('recipe').struct.unnest())
               .filter(pl.col("status").is_in(["Completed", "Conditioning"]))
               .drop('recipe', "_id")
               .sort('brewDate', descending=True))
    batches.write_csv('./Data/batches.csv')
    fermenting = (raw_batches
               .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date(), pl.col('recipe').struct.unnest())
               .filter(pl.col("status").is_in(["Fermenting", "Planned",]))
               .drop('recipe', "_id")
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
