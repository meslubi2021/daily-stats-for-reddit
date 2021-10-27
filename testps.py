print("importo la merda")
from psaw import PushshiftAPI
import praw
import utils 
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


subs = psAPI.search_submissions(after=1633821330,
                            before=1633824930,
                            subreddit="CryptoCurrency",
                            filter=['url', 'id'])

subs = list(subs)
print("fetched "+str(len(subs))+" submissions")
for sub in subs:
    print("sub: "+sub.id)
