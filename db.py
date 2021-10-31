import pymongo
import utils
import urllib
import ssl
import config_reader as config

USER = utils.get_env("DB_USER") or config.get('DB', 'USER')
password = utils.get_env("DB_PASSWORD") or config.get('DB', 'PASSWORD')
PASSWORD = urllib.parse.quote_plus(password)
DB_HOST = utils.get_env("DB_HOST") or config.get('DB', 'DB_HOST')
DB_NAME = utils.get_env("DB_NAME") or config.get('DB', 'DB_NAME')
DB_COLLECTION = utils.get_env("DB_COLLECTION") or config.get('DB', 'DB_COLLECTION')


# database configuration
URL = f"mongodb+srv://{USER}:{PASSWORD}@{DB_HOST}?retryWrites=true&w=majority"
client = pymongo.MongoClient(URL, ssl_cert_reqs=ssl.CERT_NONE)
db = client[DB_NAME]
coll_coins = db["COINS_TESTING"]#DB_COLLECTION]
coll_metadata = db["DATASET_METADATA"] #TODO

def store(coins_dict, metadata):
    # update this dataset's metadata
    coll_metadata.insert_one(metadata.asdict())
    coins = [c.__dict__ for c in coins_dict.values()]
    coll_coins.insert_many(coins)
    print("Done.")
