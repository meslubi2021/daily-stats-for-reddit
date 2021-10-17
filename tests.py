import unittest
import rcs

TEST_MESSAGES_VALID = [
    ('I like CHSB 😔', 'CHSB'),
    ('Today I bought Coin!', 'Coin'),
    ('BTC ftw', 'BTC'),
    ('Bitcoin rulez', 'Bitcoin'),
    ('I think the best coin is Just', 'Just'),
]

TEST_MESSAGES_INVALID = [
    ('Coin is a nice word', 'Coin'),
    ('Just do it', 'Just'),
    ('This coin doesn\'t exists: Buzzurro', 'Buzzurro'),
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
        for message in TEST_MESSAGES_VALID:
            comment_obj0 = MockComment(message[0])
            dict = rcs.load_crypto_collection()
            rcs.scan_and_add(dict, comment_obj0)
            self.assertTrue(dict[message[1]].count > 0)
    
    def test_scan_and_add_invalid(self):
        for message in TEST_MESSAGES_INVALID:
            comment_obj0 = MockComment(message[0])
            dict = rcs.load_crypto_collection()
            rcs.scan_and_add(dict, comment_obj0)
            self.assertFalse(message[1] in dict and dict[message[1]].count > 0)

if __name__ == '__main__':
    unittest.main()



