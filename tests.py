import unittest
import models.crypto_lizard as coins_api
import models.redditaurus as reddit

TEST_MESSAGES_VALID = [
    ('I like CHSB 😔', 'CHSB'),
    ('Today I bought Coin!', 'coin'),
    ('BTC ftw', 'BTC'),
    ('Bitcoin rulez', 'bitcoin'),
    ('there\'s no such thing as "enough" Bitcoin, ya know', 'bitcoin'),
    ('I think the best coin is Just', 'just'),
    ('bitcoin is cool', 'bitcoin'),
    ('i like Ethereum so much', 'ethereum'),
    ('bought some Fear', 'fear'),
    ('my fav: BTC, ETH, SOL', 'BTC'),
    ('my fav: BTC, ETH, SOL', 'ETH'),
    ('BTC, ETH, SOL!!', 'SOL'),
    ('neat, I like |SHIB|', 'SHIB'),
]

TEST_MESSAGES_INVALID = [
    ('have you seen that?', 'seen'),
    ('cc is the best sub', 'cc'),
    ('the best sub is CC', 'CC'),
    ('Coin is a nice word', 'coin'),
    ('i like the word coin', 'coin'),
    ('Just do it', 'just'),
    ('This coin doesn\'t exists: Buzzurro', 'buzzurro'),
    ('I like shilling', 'shilling'),
    ('no fear', 'fear'),
    ('let\'s test the blacklist with coin|coin-coin', 'coin'),
]

class MockAuthor():
    def __init__(self, name):
        self.name = name

class MockComment():
    def __init__(self, body):
        self.body = body
        self.author = MockAuthor("Spencer")
        self.created_utc = "1970-01-01"
        self.ups = 1 
        self.downs = 0
        self.total_awards_received = 0
        self.depth = 0
        self.permalink = "/test/"

class TestRCS(unittest.TestCase):
    
    def test_scan_and_add_valid(self):
        dict = coins_api.load_crypto_collection()
        for message in TEST_MESSAGES_VALID:
            comment_obj0 = MockComment(message[0])
            reddit.scan_and_add(dict, comment_obj0)
            self.assertTrue(dict[message[1]].count > 0)
    
    def test_scan_and_add_invalid(self):
        dict = coins_api.load_crypto_collection()
        for message in TEST_MESSAGES_INVALID:
            comment_obj0 = MockComment(message[0])
            reddit.scan_and_add(dict, comment_obj0)
            self.assertFalse(message[1] in dict and dict[message[1]].count > 0)

if __name__ == '__main__':
    unittest.main()



