class CoinAndCount:
    def __init__(self, name=None, count=0):
        self.name = name
        self.count = count
    
    def increment(self):
        self.count += 1