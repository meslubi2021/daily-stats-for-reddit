import unittest
import rcs

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
]

TEST_MESSAGES_INVALID = [
    ('Coin is a nice word', 'coin'),
    ('Just do it', 'just'),
    ('This coin doesn\'t exists: Buzzurro', 'buzzurro'),
    ('I like shilling', 'shilling'),
    ('no fear', 'fear'),
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

class TestRCS(unittest.TestCase):
    
    def test_scan_and_add_valid(self):
        dict = rcs.load_crypto_collection()
        for message in TEST_MESSAGES_VALID:
            comment_obj0 = MockComment(message[0])
            rcs.scan_and_add(dict, comment_obj0)
            self.assertTrue(dict[message[1]].count > 0)
    
    def test_scan_and_add_invalid(self):
        dict = rcs.load_crypto_collection()
        for message in TEST_MESSAGES_INVALID:
            comment_obj0 = MockComment(message[0])
            rcs.scan_and_add(dict, comment_obj0)
            self.assertFalse(message[1] in dict and dict[message[1]].count > 0)

if __name__ == '__main__':
    unittest.main()



