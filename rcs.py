import praw
import requests
import requests.auth
import json
import re
import time
from coin_and_count import CoinAndCount
import configparser

# config read
config = configparser.ConfigParser(allow_no_value=True)
config.read('config.ini')
CLIENT_ID = config.get('PRAW','CLIENT_ID')
CLIENT_SECRET = config.get('PRAW','CLIENT_SECRET')
SUBREDDIT = config.get('REDDIT','SUBREDDIT')

# CONST
USER_AGENT = config.get('GENERAL','USER_AGENT')
COINS_LIST_URL = config.get('GENERAL','COINS_LIST_URL')
MORE_COMMENTS_LIMIT = config.get('GENERAL','MORE_COMMENTS_LIMIT',fallback=None)
if MORE_COMMENTS_LIMIT: MORE_COMMENTS_LIMIT = int(MORE_COMMENTS_LIMIT)

print("Fetching updated list of crypto...")
headers = {
    'User-Agent': USER_AGENT
} 
coins = json.loads(requests.get(COINS_LIST_URL, headers=headers).text)

coins_dict = {}
coin_and_counts = set()

# Using a dict object to provide a duplicate key to update the values stored in the coin_and_counts
# set. This way we can increment a single counter whenever either the coin symbol OR the name are 
# mentioned. 
for coin in coins:
    coin_symbol = coin["symbol"].upper()
    coin_name = coin["name"]
    cac = CoinAndCount(name=coin_symbol)
    coin_and_counts.add(cac)
    coins_dict.update({coin_symbol : cac})
    coins_dict.update({coin_name : cac})

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
                    if word in coins_dict:
                        coins_dict[word].increment()

print("Done:\n")
for count, coin in enumerate(sorted(coin_and_counts, key = lambda x: x.count, reverse = True)):
    print(coin.name + " : " + str(coin.count))
    if count > 100:
        break
