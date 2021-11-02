import utils
import copy
import os.path
import requests
import json
import asyncio
import aiohttp
import logging
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
MARKET_CAP_API_URL = config.get('GENERAL','MARKET_CAP_URL')
SINGLE_COIN_API_URL = config.get('GENERAL','SINGLE_COIN_API_URL')
MIN_MARKET_CAP = int(config.get('GENERAL','MIN_MARKET_CAP'))
LOG_LEVEL = utils.get_env("LOG_LEVEL") or config.get('GENERAL', 'LOG_LEVEL', fallback=None)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

class CryptoLizard:

    def __init__(self):
        self.coins_dict = {}
        self.tmp_coins_dict = {}
        self.shrunk_data = {}

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
            logger.warn("File not found: " + str(fe))
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
            logger.error("Failed to fetch coins from API, falling back to latest cached file. Exception is: " + str(e))
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

    def shrink_and_sort(self):
        """
        removes unnecessary coins and returns them as a dict
        """
        # make values unique. Count and market cap must be > 0
        shrunk_data_set = set([v for v in self.tmp_coins_dict.values() if (v.count > 0 or (v.market_cap and int(v.market_cap) > 0))])
        # overwrite duplicates so that higher market cap are kept
        self.shrunk_data = {se.symbol:se for se in sorted(shrunk_data_set, key = lambda x: x.count, reverse = False)}
        return self.shrunk_data

    async def time_machine_shrunk_data(self, date):
        """
        overwrites market data with those for {date}
        """
        logger.info("Applying time machine...")
        date_str = date.strftime('%d-%m-%Y')
        return await self.bulk_update_historic_data(date_str)
        
    # get all coins sorted by ascending market cap
    def get_all_by_market_cap_asc(self):
        page = 1
        ua = utils.random_ua()
        all_coins = []
        while(True):
            with requests.Session() as s:
                logger.debug("Fetching page: " + str(page))
                params = {
                    "vs_currency": "usd",
                    "order": "market_cap_asc",
                    "per_page": 250,
                    "page": page,
                    "sparkline": "false"
                }
                headers = {
                    'User-Agent': ua
                }
                result = json.loads(s.get(MARKET_CAP_API_URL, params=params, headers=headers).text)
                # we want it sorted by mc so colliding keys will naturally overwrite lower mc coins
                result = sorted(result, key = lambda x: x["market_cap"] if "market_cap" in x and x["market_cap"] != None else 0)
                if len(result) == 0:
                    break
                page += 1

                smallest_mc = result[0]["market_cap"]
                highest_mc = result[len(result) - 1]["market_cap"]  

                if highest_mc == None or highest_mc < MIN_MARKET_CAP:
                    continue
                elif smallest_mc == None or smallest_mc < MIN_MARKET_CAP:
                    result = [c for c in result if c["market_cap"] != None and c["market_cap"] >= MIN_MARKET_CAP]

                all_coins.extend(result)
        # coins added manually are placed in the end of the array in order to overwrite any colliding ones in load_crypto_collection()
        all_coins.extend(self.get_additional_coins())
        return all_coins
        
    def get_additional_coins(self):
        ret = []    

        for c in utils.additional_coins:
            ua = utils.random_ua()
            params = {
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            headers = {
                'User-Agent': ua
            }
            coin = json.loads(requests.get(SINGLE_COIN_API_URL + c["id"], params=params, headers=headers).text)
            # overwrite name and market cap here to configure the fields as we like
            if "name" in c:
                coin["name"] = c["name"]  

            coin["image"] = coin["image"]["large"]
            coin["current_price"] = coin["market_data"]["current_price"]["usd"]
            coin["price_change_24h"] = coin["market_data"]["price_change_24h"]
            coin["price_change_percentage_24h"] = coin["market_data"]["price_change_percentage_24h"]
            coin["market_cap_change_24h"] = coin["market_data"]["market_cap_change_24h"]
            coin["market_cap_change_percentage_24h"] = coin["market_data"]["market_cap_change_percentage_24h"]
            coin["circulating_supply"] = coin["market_data"]["circulating_supply"]
            coin["total_supply"] = coin["market_data"]["total_supply"]
            coin["max_supply"] = coin["market_data"]["max_supply"]
            coin["roi"] = coin["market_data"]["roi"]
            coin["market_cap_rank"] = coin["market_data"]["market_cap_rank"]
            coin["market_cap"] = coin["market_data"]["market_cap"]["usd"]
            coin["total_volume"] = coin["market_data"]["total_volume"]["usd"]
            coin["high_24h"] = coin["market_data"]["high_24h"]["usd"]
            coin["low_24h"] = coin["market_data"]["low_24h"]["usd"]
            coin["ath"] = coin["market_data"]["ath"]["usd"]
            coin["ath_change_percentage"] = coin["market_data"]["ath_change_percentage"]["usd"]
            coin["ath_date"] = coin["market_data"]["ath_date"]["usd"]
            coin["atl"] = coin["market_data"]["atl"]["usd"]
            coin["atl_change_percentage"] = coin["market_data"]["atl_change_percentage"]["usd"]
            coin["atl_date"] = coin["market_data"]["atl_date"]["usd"]
            ret.append(coin)
        return ret
    
    async def bulk_update_historic_data(self, date_str):
        async with aiohttp.ClientSession() as session:
            for coin in self.shrunk_data.values():
                asyncio.ensure_future(self.fetch_historic_coin_data(session, coin, date_str))
                await asyncio.sleep(1.2) # limit is 50 rpm
        return self.shrunk_data

    async def fetch_historic_coin_data(self, session, original_coin, date_str):
        try:
            id = original_coin.id.lower()
            symbol = original_coin.symbol.upper()
            url = f"{SINGLE_COIN_API_URL}{id}/history"
            params = {
                "date": date_str
            }
            async with session.get(url, params=params) as resp:
                json_response = await resp.json()
                if "market_data" in json_response:
                    if "current_price" in json_response["market_data"]: 
                        self.shrunk_data[symbol].current_price = json_response["market_data"]["current_price"]["usd"]
                    if "market_cap" in json_response["market_data"]:
                        self.shrunk_data[symbol].market_cap = json_response["market_data"]["market_cap"]["usd"]
                    if "market_data" in json_response["market_data"]:
                        self.shrunk_data[symbol].total_volume = json_response["market_data"]["total_volume"]["usd"]
            logger.debug("Updated " + symbol + " with time machine for date: " + date_str)
        except Exception as ex:
            logger.warn("Error fetching history data: "+str(ex))