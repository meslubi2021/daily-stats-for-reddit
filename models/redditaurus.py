from asyncpraw.reddit import Submission
import utils
import praw
import re
import asyncpraw
import aiohttp
import asyncio
import logging
import tasker
import time as t
from models.coin_and_count import Comment
from datetime import datetime, time, timezone
import config_reader as config
from psaw import PushshiftAPI

CLIENT_ID = utils.get_env('CLIENT_ID') or config.get('PRAW', 'CLIENT_ID')
CLIENT_SECRET = utils.get_env("CLIENT_SECRET") or config.get('PRAW', 'CLIENT_SECRET')
SUBREDDIT = config.get('REDDIT', 'SUBREDDIT')
USER_AGENT = config.get('GENERAL', 'USER_AGENT')
MORE_COMMENTS_LIMIT = utils.get_env("MORE_COMMENTS_LIMIT") or config.get('GENERAL', 'MORE_COMMENTS_LIMIT', fallback=None)
LOG_LEVEL = utils.get_env("LOG_LEVEL") or config.get('GENERAL', 'LOG_LEVEL', fallback=None)
if MORE_COMMENTS_LIMIT: MORE_COMMENTS_LIMIT = int(MORE_COMMENTS_LIMIT)

CONCURRENCY_LEVEL = 10
MAX_RETRY_SUB_FETCH = 25

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

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
        self.processed_sub = 0
    
    def get_submissions_urls(self, date) -> None:
        """ Get submission urls
        function to obtain a list of submission url / id objects for a given date
        """
        date_start = int(datetime.combine(date, time.min).replace(tzinfo=timezone.utc).timestamp()) #1635465626#
        date_end = int(datetime.combine(date, time.max) .replace(tzinfo=timezone.utc).timestamp()) #1635467426#

        submissions = list(self.psAPI.search_submissions(after=date_start,
                            before=date_end,
                            subreddit=SUBREDDIT,
                            filter=['url', 'id']))  
        return submissions
    
    async def process_submissions(
            self, 
            submissions_urls, 
            crypto_lizard, 
            metadata,
            date,
            processing_date,
            cb
        ) -> None:

        """Process submissions
        The function initializes async praw and prepares a list of jobs that are
        then executed in a tasker queue w/ defined concurrency.
        This helps ensure the submission requests are not initialized all at once
        (which would cause problems like timeouts etc) 
        """

        #Initialize async praw
        self.a_reddit = asyncpraw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            requestor_kwargs={
                'session': aiohttp.ClientSession(timeout=300, connector=aiohttp.TCPConnector(limit=CONCURRENCY_LEVEL, limit_per_host=5))
            }
        )
        start_process = t.time()
        async with self.a_reddit:
            logger.info("Processing " + str(len(submissions_urls)) + " submissions.")
            self.processed_sub = 0

            # the jobs array
            jobs = [
                self.process_submission_from_url(url, crypto_lizard.get_coins_dict(), metadata)
                for url 
                in submissions_urls
            ]

            await tasker.gather_with_concurrency(*jobs)
            # return result
            await cb(crypto_lizard, metadata, date, processing_date)
            logger.info("Processed all " + str(len(submissions_urls)) + " submissions for date: " + str(date.date()) + " in " + str(int(t.time() - start_process)) + " seconds.")

    async def process_submission_from_url(
            self, 
            s, 
            coins_dict,
            metadata
        ) -> None:
        """ Process submission from url
        processes a single submission from a given url (ID).
        Here we try to work around any API errors by retrying failed connections.
        The function also calls async_grab_submission_comments to fetch and parse all the comments
        """
        retry_cnt = MAX_RETRY_SUB_FETCH

        # Fetch submission by ID
        while(retry_cnt > 0):
            await asyncio.sleep(1)
            try:
                sub = await self.a_reddit.submission(s.id)
                break
            except Exception as er:
                retry_cnt -= 1
                logger.debug("Sub fetching errored: " + str(er))
                if retry_cnt > 0:
                    logger.info("Retrying " + str(retry_cnt) + " more times.")
                else:
                    logger.error("Failed too many times fetching sub: giving up. Err: " + str(er))
                
        # add sub details to metadata
        metadata.add_num_comments(sub.num_comments)
        logger.debug("Found: " + sub.title)
        # Fetch and parse all submission comments
        await self.async_grab_submission_comments(coins_dict, sub)
        if logger.level == logging.DEBUG:
            logger.debug("Done processing submission: " + sub.title + " Dict has " + str(utils.total_count(coins_dict)) + " total counts.")
        self.processed_sub += 1

    async def async_grab_submission_comments(
            self, 
            coins_dict, 
            submission
        ) -> dict:
        """Grab submission comments
        The function fetches all comments of a submission.
        Here we try to work around any API errors by retrying failed connections.
        scan_and_add is called to parse the comments and add them to the structure coins_dict
        """

        # traversing all comments with BFS
        logger.debug("Scanning comments using limit: " + str(MORE_COMMENTS_LIMIT) + ", this may take a while...")
        start_fetch = t.time()

        retry_cnt = MAX_RETRY_SUB_FETCH
        flattened_list = []
        while(retry_cnt > 0):
            await asyncio.sleep(1)
            try:
                comments = await submission.comments()
                await comments.replace_more(limit=MORE_COMMENTS_LIMIT)
                flattened_list = await comments.list()
                break
            except Exception as er:
                retry_cnt -= 1
                logger.debug("Comment fetching errored: " + str(er))
                if retry_cnt > 0:
                    logger.info("Retrying " + str(retry_cnt) + " more times.")
                else:
                    logger.error("Failed too many times fetching comments: giving up. Err: " + str(er))
        
        time_elapsed_fetch = t.time() - start_fetch
        logger.debug("Fetched " + str(len(flattened_list)) + 
              " comments in " + str(time_elapsed_fetch) + 
              " seconds.\nParsing comments content...")
        if "Daily Discussion" in submission.title:
            logger.info("Daily Discussion has " + str(len(flattened_list)) + 
              " comments.")
        for comment in flattened_list:
            self.scan_and_add(coins_dict, comment)
        logger.debug("Parsing completed.")
        return coins_dict
    
    def scan_and_add(
            self, 
            coins_dict, 
            comment
        ) -> None:
        """ Scan and add
        Scans every comment, applies blacklists and tries to identify every coin mention.
        Comments are then added to the coins_dict structure
        """
        if comment.body:
            for word in re.split('\W+', comment.body):
                # filter out common words
                if not utils.is_uncommon(word, comment.body): continue 
                # apply blacklists
                if utils.blacklisted(word): continue 
                if comment.author == None or utils.user_blacklisted(comment.author.name): continue
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
