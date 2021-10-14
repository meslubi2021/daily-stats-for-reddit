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

# config read
config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')
CLIENT_ID = config.get('PRAW', 'CLIENT_ID')
CLIENT_SECRET = config.get('PRAW', 'CLIENT_SECRET')
SUBREDDIT = config.get('REDDIT', 'SUBREDDIT')
USER = config.get('DB', 'USER')
PASSWORD = urllib.parse.quote_plus(config.get('DB', 'PASSWORD'))
DB_HOST = config.get('DB', 'DB_HOST')
DB_NAME = config.get('DB', 'DB_NAME')
DB_COLLECTION = config.get('DB', 'DB_COLLECTION')
USER_AGENT = config.get('GENERAL', 'USER_AGENT')
COINS_LIST_URL = config.get('GENERAL', 'COINS_LIST_URL')
MORE_COMMENTS_LIMIT = config.get('GENERAL', 'MORE_COMMENTS_LIMIT', fallback=None)
if MORE_COMMENTS_LIMIT: MORE_COMMENTS_LIMIT = int(MORE_COMMENTS_LIMIT)
CACHE_CRYPTO_DICT = bool(util.strtobool(config.get('GENERAL', 'CACHE_CRYPTO_DICT')))

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
        coin_id = coin["id"]
        coin_symbol = utils.mongescape(coin["symbol"].upper()) # only match symbols that are uppercase
        coin_name = utils.mongescape(coin["name"].capitalize()) # only match names that are capitalized
        cac = CoinAndCount(name = coin_name, symbol = coin_symbol, id = coin_id)
        coins_dict.update({coin_symbol : cac})
        coins_dict.update({coin_name : cac})
    
    if CACHE_CRYPTO_DICT:
        np.save(CRYPTO_DICT_NAME, coins_dict) 
    return coins_dict

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
            print("Took: " + str(time_elapsed_fetch) + " seconds to fetch: " + str(len(flattened_list)) + " comments.\nParsing comments content...")
            for comment in flattened_list:
                if comment.body:
                    for word in re.split('\W+', comment.body):
                        word = utils.mongescape(word)
                        if word in coins_dict:
                            coins_dict[word].increment()
                            my_comment = Comment(comment.author.name, comment.created_utc, comment.ups, comment.downs, comment.total_awards_received)
                            coins_dict[word].comments.append(my_comment.__dict__)

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

def print_sample_output(coins_dict):
    coin_and_counts = set(coins_dict.values())
    for count, coin in enumerate(sorted(coin_and_counts, key = lambda x: x.count, reverse = True)):
        print(coin.name + "(" + coin.symbol + "): " + str(coin.count))
        if count > 100:
            break

if __name__ == "__main__":
    print("Fetching updated list of crypto...")
    coins_dict = load_crypto_collection()
    print("Searching Reddit for crypto mentions")
    search_reddit(coins_dict)
    if args.print:
        print("Done:\n")
        print_sample_output(coins_dict)
    if args.writedb:
        store_to_db(coins_dict)


