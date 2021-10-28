import utils
import praw
import re
import asyncpraw
import aiohttp
import asyncio
import db
import time as t
from coin_and_count import CoinAndCount, Comment
from datetime import datetime, timezone, time
import config_reader as config
from psaw import PushshiftAPI

CLIENT_ID = utils.get_env('CLIENT_ID') or config.get('PRAW', 'CLIENT_ID')
CLIENT_SECRET = utils.get_env("CLIENT_SECRET") or config.get('PRAW', 'CLIENT_SECRET')
SUBREDDIT = config.get('REDDIT', 'SUBREDDIT')
USER_AGENT = config.get('GENERAL', 'USER_AGENT')
MORE_COMMENTS_LIMIT = utils.get_env("MORE_COMMENTS_LIMIT") or config.get('GENERAL', 'MORE_COMMENTS_LIMIT', fallback=None)
if MORE_COMMENTS_LIMIT: MORE_COMMENTS_LIMIT = int(MORE_COMMENTS_LIMIT)

CONCURRENCY_LEVEL = 10
MAX_RETRY_SUB_FETCH = 25

class Redditaurus:
    def __init__(self):

        # praw
        self.reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT
        )
        # psaw
        self.psAPI = PushshiftAPI(self.reddit)
    
    def get_submissions_urls(self, date) -> None:
        date_start = int(datetime.combine(date, time.min).replace(tzinfo=timezone.utc).timestamp())
        date_end = int(datetime.combine(date, time.max) .replace(tzinfo=timezone.utc).timestamp())

        submissions = list(self.psAPI.search_submissions(after=date_start,
                            before=date_end,
                            subreddit=SUBREDDIT,
                            filter=['url', 'id']))
                                     
        return submissions
    
    async def process_submissions(
            self, 
            submissions_urls, 
            coins_dict, 
            cb
        ) -> None:

        self.a_reddit = asyncpraw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            requestor_kwargs={
                'session': aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=CONCURRENCY_LEVEL))
            }
        )
        print("Processing " + str(len(submissions_urls)) + " submissions.")

        async with self.a_reddit:
            jobs = set()
            for url in submissions_urls:
                jobs.add(
                    asyncio.create_task(
                        self.process_single_submission_from_url(url, coins_dict)
                    )
                )
            await asyncio.gather(*jobs)
        #for url in submissions_urls:
        #    await self.process_single_submission_from_url(url, coins_dict)
        self.aggregate_submission_data(coins_dict, cb)

    async def process_single_submission_from_url(
            self, 
            s, 
            coins_dict
        ) -> None:
        
        retry_cnt = MAX_RETRY_SUB_FETCH

        while(retry_cnt > 0):
            try:
                sub = await self.a_reddit.submission(s.id)
                retry_cnt = 0
                db.add_dataset_details(coins_dict, sub)
                print("Found: " + sub.title)
                await self.async_grab_submission_comments(coins_dict, sub)
            except Exception as er:
                retry_cnt -= 1
                print("Sub fetching errored: " + str(er))
                if retry_cnt > 0:
                    print("Retrying " + str(retry_cnt) + " more times.")
        
    def aggregate_submission_data(
            self, 
            data, 
            callback
        ) -> None:

        coin_and_counts = set([v for v in data.values() if isinstance(v, CoinAndCount) 
                                and (v.count > 0 or (v.market_cap and int(v.market_cap) > 0))])
        d = {se.symbol:se for se in sorted(coin_and_counts, key = lambda x: x.count, reverse = False)}
        d.update({k:data[k] for k in data if not isinstance(data[k], CoinAndCount)})
        callback(d)

    async def async_grab_submission_comments(
            self, 
            coins_dict, 
            submission
        ) -> dict:

        # traversing all comments with BFS
        print("Scanning comments, this may take a while...")
        start_fetch = t.time()
        comments = await submission.comments()
        await comments.replace_more(limit=MORE_COMMENTS_LIMIT)
        flattened_list = await comments.list()
        time_elapsed_fetch = t.time() - start_fetch
        print("Fetched " + str(len(flattened_list)) + 
              " comments in " + str(time_elapsed_fetch) + 
              " seconds.\nParsing comments content...")
        for comment in flattened_list:
            self.scan_and_add(coins_dict, comment)
        print("Parsing completed.")
        return coins_dict
    
    def scan_and_add(
            self, 
            coins_dict, 
            comment
        ) -> None:

        if comment.body:
            for word in re.split('\W+', comment.body):
                # filter out common words
                if not utils.is_uncommon(word, comment.body): continue 
                # apply blacklist
                if utils.blacklisted(word): continue 
                word = utils.mongescape(word)
                # lower words that are not completely upper
                if not word.isupper(): word = word.lower() 
                if word in coins_dict:
                    coins_dict[word].increment()
                    my_comment = Comment(
                        comment.author.name, 
                        comment.created_utc, 
                        comment.ups, 
                        comment.downs, 
                        comment.total_awards_received, 
                        comment.body, 
                        comment.depth, 
                        comment.permalink
                    )
                    coins_dict[word].comments.append(my_comment.__dict__)
