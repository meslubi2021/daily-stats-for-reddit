print("importo la merda")
from psaw import PushshiftAPI
import praw
import utils 
from datetime import datetime, time, timezone
import config_reader as config 

print("fetching subs")
CLIENT_ID = utils.get_env('CLIENT_ID') or config.get('PRAW', 'CLIENT_ID')
CLIENT_SECRET = utils.get_env("CLIENT_SECRET") or config.get('PRAW', 'CLIENT_SECRET')
USER_AGENT = config.get('GENERAL', 'USER_AGENT')

reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT
        )

print("creato reddit")
print("client id "+ CLIENT_ID)
print("client sec "+ CLIENT_SECRET)
print("user agent "+ USER_AGENT)


print("creating api")
psAPI = PushshiftAPI(reddit)

today = datetime.today()
date_start = datetime.combine(today, time.min) 
date_end = datetime.combine(today, time.max)
date_start = int(date_start.replace(tzinfo=timezone.utc).timestamp())
date_end = int(date_end.replace(tzinfo=timezone.utc).timestamp())

subs = list(psAPI.search_submissions(after=date_start,
                            before=date_end,
                            subreddit="CryptoCurrency",
                            filter=['url', 'id']))

print("fetched "+str(len(subs))+" submissions")
for sub in subs:
    print("sub: "+sub.id)
