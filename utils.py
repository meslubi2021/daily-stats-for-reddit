import requests
import configparser
import json

config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')

USER_AGENT = config.get('GENERAL','USER_AGENT')
MARKET_CAP_API_URL = config.get('GENERAL','MARKET_CAP_URL')

def sort_by_market_cap(ids):
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
        'User-Agent': USER_AGENT
    }
    result = json.loads(requests.get(MARKET_CAP_API_URL, params=params, headers=headers).text)
    return [x['id'] for x in result]
