import utils
import config_reader as config
import numpy as np
from distutils import util
from coin_and_count import CoinAndCount

CACHE_CRYPTO_DICT = utils.get_env("CACHE_CRYPTO_DICT") or bool(util.strtobool(config.get('GENERAL', 'CACHE_CRYPTO_DICT')))
CRYPTO_DICT_NAME = "res/crypto_list.npy"

# downloads the crypto list and loads it in a dictionary with the appropriate keys to scan
# the comments.
def load_crypto_collection():
    coins_dict = {}
    # attempt to fetch the cached crypto dict, if configured and if available:
    if CACHE_CRYPTO_DICT:
        try:
            coins_dict = np.load(CRYPTO_DICT_NAME,allow_pickle='TRUE').item()
            if coins_dict:
                return coins_dict
        except FileNotFoundError:
            pass

    # coins are fetched already sorted by market cap ascending so that the last that are added 
    # to the dictionary overwrite automatically any duplicate name or symbol keys of
    # less popular coins. This way when a certain "duplicate" name or symbol is mentioned,
    # we will count it as the most popular (more likely to be mentioned) coin.
    coins = utils.get_all_by_market_cap_asc()

    # Using a dict object to provide a duplicate key to update the values stored in the coin_and_counts
    # set. This way we can increment a single counter whenever either the coin symbol OR the name are 
    # mentioned. 
    for coin in coins:
        coin_symbol = utils.mongescape(coin['symbol'].upper()) # only match symbols that are uppercase
        coin_name = utils.mongescape(coin['name'].lower())
        cac = CoinAndCount(coin_name, coin_symbol, coin = coin)
        coins_dict.update({coin_symbol : cac})
        coins_dict.update({coin_name : cac})
    np.save(CRYPTO_DICT_NAME, coins_dict) 
    return coins_dict