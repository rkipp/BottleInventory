import polars as pl
import requests
from requests.auth import HTTPBasicAuth
from apikey import userid, apikey

# Constants
oz_p_liter = (1/33.8140227)
oz_p_gram  = (1/0.0352739619)
lbs_p_kilo = (1/2.20462)

def update_batches():
    auth = HTTPBasicAuth(userid, apikey)
    batches = pl.DataFrame(requests.get('https://api.brewfather.app/v2/batches?limit=50&order_by=batchNo', auth=auth).json())
    
    batches = (batches
               .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date(), pl.col('recipe').struct.unnest())
               .filter(pl.col("status").is_in(["Completed", "Conditioning"]))
               .drop('recipe', "_id")
               .sort('brewDate', descending=True))
    batches.write_csv('./Data/batches.csv')

def get_whats_fermenting():
    auth = HTTPBasicAuth(userid, apikey)
    batches = pl.DataFrame(requests.get('https://api.brewfather.app/v2/batches?limit=50&order_by=batchNo', auth=auth).json())
    
    batches = (batches
               .with_columns(pl.from_epoch('brewDate', time_unit='ms').dt.date(), pl.col('recipe').struct.unnest())
               .filter(pl.col("status").is_in(["Fermenting"]))
               .drop('recipe', "_id")
               .sort('brewDate', descending=True))
    return batches
    

def get_batches():
    batches = pl.read_csv('./Data/batches.csv')
    return batches

if __name__ == "__main__":
    update_batches()
    print(get_batches())
