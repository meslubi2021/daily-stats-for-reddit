import requests
import configparser
import json
import re
import os
import logging
from datetime import timedelta, datetime, time
from time import sleep
from random import choice, uniform

from models.coin_and_count import CoinAndCount

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

LOG_LEVEL = {
    "CRITICAL" : logging.CRITICAL,
    "ERROR" : logging.ERROR,
    "WARNING" : logging.WARNING,
    "INFO" : logging.INFO,
    "DEBUG" : logging.DEBUG
    }

def rand_sleep(start, end):
    sleep(uniform(start, end))

def random_ua():
    return choice(USER_AGENTS)

def get_date_range(range_string):
    if range_string == None:
        return [datetime.today()]
    range = []
    range_string = range_string.strip()
    date_range = [datetime.strptime(d, "%d/%m/%Y") for d in range_string.split("-")]
    date_start, date_end = date_range[0], date_range[len(date_range) - 1]
    while(date_start <= date_end):
        range.append(date_start)
        date_start = date_start + timedelta(days=1)
    return range

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

def total_count(coins_dict):
    counter = 0
    for v in coins_dict.values():
        if isinstance(v, CoinAndCount):
            counter += v.count
    return counter

def blacklisted(w):
    return w in BLACKLIST

def user_blacklisted(u):
    for bl in USERS_BLACKLIST:
        if u.lower().startswith(bl.lower()) or u.lower().endswith(bl.lower()):
            return True
    return False

USERS_BLACKLIST = [
    "bot",
    "automoderator"
]

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
    'Cryptocurrency',
    'BAN'
]