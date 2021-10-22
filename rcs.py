import praw
import re
import time
import configparser
import utils
import pymongo
import urllib
import ssl
from distutils import util
from coin_and_count import CoinAndCount, Comment
from argparse import ArgumentParser
import numpy as np
import os

# Due to the high amount of cryptos that share names or symbol that are commonly used,
# the script can't always return reliable results. The algorithms trade accuracy for 
# lower amount of false positives while the following rules are applied:
# [1] Only symbol that are completely uppercase are matched
# [2] Common English words are ignored unless they seem to be intentionally capitalized
# [3] Oh and we have a blacklist

# config read
config = configparser.ConfigParser(allow_no_value=True)
config_file = "config.ini"
if not os.path.isfile(config_file):
    config_file = "config.ini-dist"
config.read(config_file)

CLIENT_ID = utils.get_env('CLIENT_ID') or config.get('PRAW', 'CLIENT_ID')
CLIENT_SECRET = utils.get_env("CLIENT_SECRET") or config.get('PRAW', 'CLIENT_SECRET')
SUBREDDIT = config.get('REDDIT', 'SUBREDDIT')
USER = utils.get_env("USER") or config.get('DB', 'USER')
PASSWORD = utils.get_env("PASSWORD") or urllib.parse.quote_plus(config.get('DB', 'PASSWORD'))
DB_HOST = utils.get_env("DB_HOST") or config.get('DB', 'DB_HOST')
DB_NAME = utils.get_env("DB_NAME") or config.get('DB', 'DB_NAME')
DB_COLLECTION = config.get('DB', 'DB_COLLECTION')
USER_AGENT = config.get('GENERAL', 'USER_AGENT')
COINS_LIST_URL = config.get('GENERAL', 'COINS_LIST_URL')
MORE_COMMENTS_LIMIT = utils.get_env("MORE_COMMENTS_LIMIT") or config.get('GENERAL', 'MORE_COMMENTS_LIMIT', fallback=None)
if MORE_COMMENTS_LIMIT: MORE_COMMENTS_LIMIT = int(MORE_COMMENTS_LIMIT)
CACHE_CRYPTO_DICT = utils.get_env("CACHE_CRYPTO_DICT") or bool(util.strtobool(config.get('GENERAL', 'CACHE_CRYPTO_DICT')))

# other const
CRYPTO_DICT_NAME = "crypto_list.npy"

# database configuration
URL = f"mongodb+srv://{USER}:{PASSWORD}@{DB_HOST}?retryWrites=true&w=majority"
client = pymongo.MongoClient(URL, ssl_cert_reqs=ssl.CERT_NONE)
db = client[DB_NAME]
coins_collection = db[DB_COLLECTION]

# arg parsing
parser = ArgumentParser()
parser.add_argument("-w", "--write", dest="writedb", action='store_true',
                    help="write to DB.")
parser.add_argument("-p", "--print", dest="print", action='store_true',
                    help="print result to console.")                  
args = parser.parse_args()

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

def scan_and_add(coins_dict, comment):
    if comment.body:
        for word in re.split('\W+', comment.body):
            if not utils.is_uncommon(word, comment.body): continue # filter out common words
            if utils.blacklisted(word): continue # apply blacklist
            word = utils.mongescape(word)
            if not word.isupper(): word = word.lower() # lower words that are not completely upper
            if word in coins_dict:
                coins_dict[word].increment()
                my_comment = Comment(comment.author.name, comment.created_utc, comment.ups, 
                                     comment.downs, comment.total_awards_received)
                coins_dict[word].comments.append(my_comment.__dict__)

def search_reddit(coins_dict):
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
    )
    subreddit = reddit.subreddit(SUBREDDIT)
    print("Selected subreddit: " + subreddit.display_name)
    print("Searching Daily Discussion...")
    # scan first 10 hot submission, looking for the daily
    for submission in subreddit.hot(limit=10):
        if "Daily Discussion" in submission.title:
            print("Found: " + submission.title)
            # traversing all comments with BFS
            print("Scanning comments, this may take a while...")
            start_fetch = time.time()
            submission.comments.replace_more(limit=MORE_COMMENTS_LIMIT)
            time_elapsed_fetch = time.time() - start_fetch
            flattened_list = submission.comments.list()
            print("Fetched " + str(len(flattened_list)) + " comments in " + str(time_elapsed_fetch) + 
                  " seconds.\nParsing comments content...")
            for comment in flattened_list:
                scan_and_add(coins_dict, comment)
                
def store_to_db(coins_dict):
    r = coins_dict
    for k, v in r.items():   
        r[k] = v.__dict__
    try:
        coins_collection.insert_one(r)
    except pymongo.errors.InvalidDocument:
        n = {}
        for k, v in r.items():
            if isinstance(v, CoinAndCount):
                for va in v.comments:
                    if isinstance(va, Comment):
                        print(str(va.ups))
                        va.timestamp = str(va.timestamp).encode("utf-8")
                        va.ups = str(va.ups).encode("utf-8")
                        va.downs = str(va.downs).encode("utf-8")
                        va.total_awards_received = str(va.total_awards_received).encode("utf-8")
                        va.author_name = va.author_name.encode("utf-8")
            print(str(type(v)))
            n[k] = v
        coins_collection.insert_one(n)
    finally:
        print("Done.")

def print_sample_output(coin_and_counts):
    output = ""
    for count, coin in enumerate(sorted(coin_and_counts, key = lambda x: x.count, reverse = True)):
        s_out = coin.name + "(" + coin.symbol + "): " + str(coin.count)
        print(s_out)
        output += "\n" + s_out
        if count > 100:
            break
        with open("output.txt", "w") as text_file:
            text_file.write(output)

if __name__ == "__main__":
    print("Fetching updated list of crypto...")
    coins_dict = load_crypto_collection()
    print("Searching Reddit for crypto mentions")
    search_reddit(coins_dict)
    coin_and_counts = set([v for v in coins_dict.values() if v.count > 0])
    if args.print:
        print("Done:\n")
        print_sample_output(coin_and_counts)
    if args.writedb:
        print("Storing to DB...\n")
        d = {se.symbol:se for se in coin_and_counts}
        store_to_db(d)


