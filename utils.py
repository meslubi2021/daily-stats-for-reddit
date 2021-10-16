import requests
import configparser
import json
import time
from time import sleep
from random import choice, uniform

config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')

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
        time.sleep(0.5)
        print("Fetching page: "+str(page))
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
        result = json.loads(requests.get(MARKET_CAP_API_URL, params=params, headers=headers).text)
        if len(result) == 0:
            break
        page += 1
        mc = result[len(result)-1]["market_cap"]
        if mc and mc < MIN_MARKET_CAP:
            continue
        all_coins.extend(result)
    return all_coins

def mongescape(w):
    return w.replace("$", "[S]")

# returns true for words that seem to be intentionally capitalized
def is_unnaturally_capital(w, s):
    if not w or not w[0].isupper:
        return False
    s_dot_split = s.split(".")
    for w_s in s_dot_split:
        for word_check in w_s.strip().split(" ")[1:]:
            if word_check == w:
                return True
    return False

def blacklisted(w):
    return w in BLACKLIST

BLACKLIST = [
    'NFT',
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
    'FOMO'
]