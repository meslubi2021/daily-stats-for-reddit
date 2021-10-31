import utils
import copy
import os.path
from datetime import datetime, time, timezone
import config_reader as config
import numpy as np
from distutils import util
from models.coin_and_count import CoinAndCount

"""
Class that fetches and handles the coins dict that will be used to keep
track of all counters.
"""
CACHE_CRYPTO_DICT = utils.get_env("CACHE_CRYPTO_DICT") or bool(util.strtobool(config.get('GENERAL', 'CACHE_CRYPTO_DICT')))
CRYPTO_DICT_NAME = os.path.dirname(__file__) + "/../res/crypto_list.npy"

class CryptoLizard:

    def __init__(self):
        self.coins_dict = {}
        self.tmp_coins_dict = {}

    def get_coins_dict(self) -> dict:
        return self.tmp_coins_dict
    
    def reset_coins_dict(self) -> dict:
        self.tmp_coins_dict = copy.deepcopy(self.coins_dict)

    def load_local_crypto_list(self) -> dict:
        try:
            self.coins_dict = np.load(CRYPTO_DICT_NAME, allow_pickle='TRUE').item()
            if self.coins_dict:
                self.reset_coins_dict()
        except FileNotFoundError as fe:
            print(fe)
            print("File not found.")
        return self.get_coins_dict()

    # downloads the crypto list and loads it in a dictionary with the appropriate keys to scan
    # the comments.
    def load_crypto_collection(self) -> dict:
        # attempt to fetch the cached crypto dict, if configured and if available:
        if CACHE_CRYPTO_DICT:
            local_crypto_list = self.load_local_crypto_list()
            if len(local_crypto_list) > 0:
                return local_crypto_list

        # coins are fetched already sorted by market cap ascending so that the last that are added 
        # to the dictionary overwrite automatically any duplicate name or symbol keys of
        # less popular coins. This way when a certain "duplicate" name or symbol is mentioned,
        # we will count it as the most popular (more likely to be mentioned) coin.
        try:
            coins = utils.get_all_by_market_cap_asc()
        except Exception as e:
            print(e)
            print("Failed to fetch coins from API, falling back to latest cached file.")
            return self.load_local_crypto_list()

        # Using a dict object to provide a duplicate key to update the values stored in the coin_and_counts
        # set. This way we can increment a single counter whenever either the coin symbol OR the name are 
        # mentioned. 
        for coin in coins:
            coin_symbol = utils.mongescape(coin['symbol'].upper()) # only match symbols that are uppercase
            coin_name = utils.mongescape(coin['name'].lower())
            cac = CoinAndCount(coin_name, coin_symbol, coin = coin)
            self.coins_dict.update({coin_symbol : cac})
            self.coins_dict.update({coin_name : cac})
        np.save(CRYPTO_DICT_NAME, self.coins_dict) 
        self.reset_coins_dict()
        return self.get_coins_dict()

    def timestamp_tag_crypto_collection(self, date):
        ts = int(datetime.combine(date, time.min).replace(tzinfo=timezone.utc).timestamp())
        for k in self.tmp_coins_dict:
            self.tmp_coins_dict[k].set_timestamp(ts)

    
    def dataset_id_tag_crypto_collection(self, id):
        for k in self.tmp_coins_dict:
            self.tmp_coins_dict[k].set_dataset_id(id)

        
        