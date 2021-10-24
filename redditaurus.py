import utils
import praw
import time
import re
from coin_and_count import Comment
from datetime import datetime
import config_reader as config


CLIENT_ID = utils.get_env('CLIENT_ID') or config.get('PRAW', 'CLIENT_ID')
CLIENT_SECRET = utils.get_env("CLIENT_SECRET") or config.get('PRAW', 'CLIENT_SECRET')
SUBREDDIT = config.get('REDDIT', 'SUBREDDIT')
USER_AGENT = config.get('GENERAL', 'USER_AGENT')
DAILY_DATE_RANGE = utils.get_env("DAILY_DATE_RANGE") or config.get('GENERAL', 'DAILY_DATE_RANGE')
MORE_COMMENTS_LIMIT = utils.get_env("MORE_COMMENTS_LIMIT") or config.get('GENERAL', 'MORE_COMMENTS_LIMIT', fallback=None)
if MORE_COMMENTS_LIMIT: MORE_COMMENTS_LIMIT = int(MORE_COMMENTS_LIMIT)

# reddit stuff
reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
    )
subreddit = reddit.subreddit(SUBREDDIT)

def latest_daily(coins_dict, callback):
    print("Searching Latest Daily Discussion...")
    # scan first 10 hot submission, looking for today's daily
    for submission in subreddit.hot(limit=10):
        if "Daily Discussion" in submission.title:
            print("Found: " + submission.title)
            d = grab_submission_comments(coins_dict, submission)
            process_output(d, submission, callback)

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
                                     comment.downs, comment.total_awards_received, comment.body, 
                                     comment.depth, comment.permalink)
                coins_dict[word].comments.append(my_comment.__dict__)

def process_output(data, sub, callback):
    coin_and_counts = set([v for v in data.values() if v.count > 0 or (v.market_cap and int(v.market_cap) > 0)])
    d = {se.symbol:se for se in coin_and_counts}
    d['_submission_timestamp'] = str(sub.created_utc)
    callback(d)

def range_dailies(coins_dict, callback):
    print("Searching Range of Daily Discussion...")
    date_range = DAILY_DATE_RANGE.split("-")
    date_range = [datetime.strptime(d, "%d/%m/%Y").date() for d in date_range]
    dates = utils.get_dates_in_range(date_range[0], date_range[len(date_range) - 1])
    daily_titles = [utils.generate_daily_title_format(date) for date in dates]
    for daily_title in daily_titles:
        for submission in subreddit.search(daily_title):
            print("Found: " + submission.title)
            d = grab_submission_comments(coins_dict, submission)
            process_output(d, submission, callback)

def grab_submission_comments(coins_dict, submission):
    # traversing all comments with BFS
    print("Scanning comments, this may take a while...")
    start_fetch = time.time()
    submission.comments.replace_more(limit = MORE_COMMENTS_LIMIT)
    time_elapsed_fetch = time.time() - start_fetch
    flattened_list = submission.comments.list()
    print("Fetched " + str(len(flattened_list)) + " comments in " + str(time_elapsed_fetch) + 
          " seconds.\nParsing comments content...")
    for comment in flattened_list:
        scan_and_add(coins_dict, comment)
    return coins_dict