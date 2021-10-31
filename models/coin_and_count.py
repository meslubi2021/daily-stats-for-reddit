
class CoinAndCount:

    def __init__(self, name, symbol, coin=None, count = 0, dataset_timestamp = -1, dataset_id = None):
        self.symbol = symbol 
        self.name = name
        self.count = count
        self.comments = []
        self.id = coin['id']
        self._dataset_timestamp = dataset_timestamp
        self._dataset_id = dataset_id

        # non mandatory fields
        try:
            self.image = coin['image']
            self.current_price = coin['current_price']
            self.market_cap = coin['market_cap']
            self.market_cap_rank = coin['market_cap_rank']
            self.total_volume = coin['total_volume']
            self.high_24h = coin['high_24h']
            self.low_24h = coin['low_24h']
            self.price_change_24h = coin['price_change_24h']
            self.price_change_percentage_24h = coin['price_change_percentage_24h']
            self.market_cap_change_24h = coin['market_cap_change_24h']
            self.market_cap_change_percentage_24h = coin['market_cap_change_percentage_24h']
            self.circulating_supply = coin['circulating_supply']
            self.total_supply = coin['total_supply']
            self.max_supply = coin['max_supply']
            self.ath = coin['ath']
            self.ath_change_percentage = coin['ath_change_percentage']
            self.ath_date = coin['ath_date']
            self.atl = coin['atl']
            self.atl_change_percentage = coin['atl_change_percentage']
            self.atl_date = coin['atl_date']
            self.roi = coin['roi']
        except KeyError:
            pass
        
    def set_timestamp(self, ts):
        self._dataset_timestamp = ts
    
    def set_dataset_id(self, id):
        self._dataset_id = id

    def increment(self):
        self.count += 1


class Comment:
    def __init__(self, author_name=None, timestamp=None, ups=None, downs=None, total_awards_received=None,
                 body=None, depth=0, permalink=None):
        self.timestamp = timestamp
        self.ups = ups
        self.downs = downs
        self.total_awards_received = total_awards_received
        self.author_name = author_name
        self.body = body
        self.depth = depth
        self.permalink = permalink
