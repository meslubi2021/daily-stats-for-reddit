class CoinAndCount:
    def __init__(self, name=None, symbol=None, id=None, count=0):
        self.name = name
        self.symbol = symbol
        self.id = id
        self.count = count
        self.comments = []
        
    def increment(self):
        self.count += 1


class Comment:
    def __init__(self, author_name=None, timestamp=None, ups=None, downs=None, total_awards_received=None):
        self.timestamp = timestamp
        self.ups = ups
        self.downs = downs
        self.total_awards_received = total_awards_received
        self.author_name = author_name
