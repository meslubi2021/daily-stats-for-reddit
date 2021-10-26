import requests
import configparser
import json
import re
import os
from datetime import timedelta
from time import sleep
from random import choice, uniform

config = configparser.ConfigParser(allow_no_value=True)
config_file = "config.ini"
if not os.path.isfile(config_file):
    config_file = "config.ini-dist"
config.read(config_file)
common_words_dictionary = {}

with open("res/common_words.json", "r") as common_words:
    common_words_dictionary = json.load(common_words)

with open("res/additional_coins.json", "r") as other_coins:
    additional_coins = (json.load(other_coins))

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
]

MARKET_CAP_API_URL = config.get('GENERAL','MARKET_CAP_URL')
SINGLE_COIN_API_URL = config.get('GENERAL','SINGLE_COIN_API_URL')
MIN_MARKET_CAP = int(config.get('GENERAL','MIN_MARKET_CAP'))

def rand_sleep(start, end):
    sleep(uniform(start, end))

def random_ua():
    return choice(USER_AGENTS)

# unused
def sort_by_market_cap(ids):
    rand_sleep(0,2)
    ids_str = ",".join(ids)
    params = {
        "vs_currency": "usd",
        "ids": ids_str,
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }
    headers = {
        'User-Agent': random_ua()
    }
    result = json.loads(requests.get(MARKET_CAP_API_URL, params=params, headers=headers).text)
    return [x['id'] for x in result]

# get all coins sorted by ascending market cap
def get_all_by_market_cap_asc():
    page = 1
    ua = random_ua()
    all_coins = []
    while(True):
        with requests.Session() as s:
            print("Fetching page: " + str(page))
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
    all_coins.extend(get_additional_coins())
    return all_coins

def mongescape(w):
    return w.replace("$", "[S]")

# returns true for words that seem to be uncommon enough to be
# considered coin mentions
def is_uncommon(w, body):
    # check capitalized words
    if not w:
        return False
    body = re.sub("[^a-zA-Z\d\s:\.]", " ", body)
    b_split = re.split("\.\s*|\n", body)
    for sentence in b_split:
        for index, word in enumerate(sentence.strip().split(" ")):
            if word == w:
                # each word at index 0 is expected to be capitalized
                if (index == 0 or not w[0].isupper()) and word.lower() in common_words_dictionary:
                    return False
    return True

def get_env(ENV):
    try:
        return os.environ[ENV]
    except KeyError:
        return ""

def generate_daily_title_format(date):
    return "Daily Discussion - " + str(date.strftime("%B")) + " " + str(date.day) + ", " + date.strftime("%Y") + " (GMT+0)"

def get_dates_in_range(date_start, date_end):
    date_range = [date_start]
    while(date_start < date_end):
        date_start += timedelta(days=1)
        date_range.append(date_start)
    return date_range

def get_additional_coins():
    ret = []    
    
    for c in additional_coins:
        ua = random_ua()
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

def blacklisted(w):
    return w in BLACKLIST

def add_dataset_details(coins_dict, sub):
    if not '_dataset_timestamp' in coins_dict:
        coins_dict['_dataset_timestamp'] = str(sub.created_utc)
    if not '_dataset_num_comments' in coins_dict:
        coins_dict['_dataset_num_comments'] = sub.num_comments
    else:
        coins_dict['_dataset_num_comments'] += sub.num_comments

BLACKLIST = [
    'NFT',
    'QC',
    'YT',
    'DCA',
    'ETF',
    'YES',
    'HODL',
    'U',
    'APY',
    'IT',
    'HODL',
    'LOL',
    'CC',
    'X',
    'D',
    'DEX',
    'PUMP',
    'ATH',
    'FOMO',
    'CMC',
    'Cryptocurrency'
]