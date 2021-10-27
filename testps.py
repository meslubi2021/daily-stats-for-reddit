print("importo la merda")
from psaw import PushshiftAPI
        

print("creating api")
psAPI = PushshiftAPI()
print("fetching subs")
subs = psAPI.search_submissions(after=1633821330,
                            before=1633824930,
                            subreddit="CryptoCurrency",
                            filter=['url', 'id'])

subs = list(subs)
print("fetched "+str(len(subs))+" submissions")
for sub in subs:
    print("sub: "+sub.id)
