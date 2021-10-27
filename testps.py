from psaw import PushshiftAPI
        
psAPI = PushshiftAPI()

psAPI.search_submissions(after=1633821330,
                            before=1633824930,
                            subreddit="CryptoCurrency",
                            filter=['url', 'id'])


