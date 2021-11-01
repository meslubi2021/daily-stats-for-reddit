import utils
import db
import asyncio
import logging
from datetime import datetime, time, timezone
from models.ds_metadata import DatasetMetadata
from models.crypto_lizard import CryptoLizard
import config_reader as config
from argparse import ArgumentParser
import models.redditaurus as reddit
from models.coin_and_count import CoinAndCount

# Due to the high amount of cryptos that share names or symbol that are commonly used,
# the script can't always return reliable results. The algorithms trade accuracy for 
# lower amount of false positives while the following rules are applied:
# [1] Only symbols that are completely uppercase are matched
# [2] Common English words are ignored unless they seem to be intentionally capitalized
# [3] Oh and we have a blacklist

COINS_LIST_URL = config.get('GENERAL', 'COINS_LIST_URL')
DAILY_DATE_RANGE = utils.get_env("DAILY_DATE_RANGE") or config.get('GENERAL', 'DAILY_DATE_RANGE')
LOG_LEVEL = utils.get_env("LOG_LEVEL") or config.get('GENERAL', 'LOG_LEVEL', fallback=None)

logger = logging.getLogger(__name__)
logger.setLevel(utils.LOG_LEVEL[LOG_LEVEL])
logging.basicConfig(level=utils.LOG_LEVEL[LOG_LEVEL])

# arg parsing
parser = ArgumentParser()
parser.add_argument("-w", "--write", dest="writedb", action='store_true',
                    help="write to DB.")
parser.add_argument("-p", "--print", dest="print", action='store_true',
                    help="print result to console.") 
parser.add_argument("-r", "--range", dest="range", action='store',
                    help="date range in the format dd/mm/yyyy[-dd/mm/yyyy].")                 
args = parser.parse_args()

def print_sample_output(coin_and_counts):
    output = ""
    for index, coin_t in enumerate(sorted(coin_and_counts.items(), key = lambda x: x[1].count if isinstance(x[1], CoinAndCount) else 0, reverse = True)):
        coin = coin_t[1]
        s_out = coin.name.capitalize() + " (" + coin.symbol + "): " + str(coin.count)
        print(s_out)
        output += "\n" + s_out
        if index > 100:
            break
        with open("output.txt", "w") as text_file:
            text_file.write(output)

async def process_data(crypto_lizard, dataset_metadata, date, processing_date):
    data = crypto_lizard.shrink_and_sort()
    if date.date() != processing_date.date():
        data = await crypto_lizard.time_machine_shrunk_data(date)
    if args.print:
        logger.info("Done:\n")
        print_sample_output(data)
    if args.writedb:
        logger.info("Storing to DB...\n")
        db.store(data, dataset_metadata)

if __name__ == "__main__":
    crypto_lizard = CryptoLizard()
    crypto_lizard.load_crypto_collection()
    rt = reddit.Redditaurus()
    dates = utils.get_date_range(args.range)
    for date in dates:
        print("Fetching data for date: " + str(date))
        metadata = DatasetMetadata(dataset_timestamp=int(datetime.combine(date, time.min).replace(tzinfo=timezone.utc).timestamp()))
        crypto_lizard.reset_coins_dict()
        crypto_lizard.timestamp_tag_crypto_collection(date)
        crypto_lizard.dataset_id_tag_crypto_collection(metadata._dataset_id)
        logger.info("Fetching submission urls...")
        urls = rt.get_submissions_urls(date)
        logger.info("Fetching everything from subs...")
        asyncio.run(rt.process_submissions(urls, crypto_lizard, metadata, date, datetime.today(), process_data))