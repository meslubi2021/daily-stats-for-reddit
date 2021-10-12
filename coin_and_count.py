class CoinAndCount:
    def __init__(self, name=None, symbol=None, id=None, count=0):
        self.name = name
        self.symbol = symbol
        self.id = id
        self.count = count
    
    def increment(self):
        self.count += 1