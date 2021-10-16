import unittest

from numpy import UFUNC_PYVALS_NAME
import rcs

TEST_MESSAGES = [
    ('I like CHSB 😔', 'CHSB')
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
    
    def test_scan_and_add(self):
        for message in TEST_MESSAGES:
            comment_obj0 = MockComment(message[0])
            dict = rcs.load_crypto_collection()
            rcs.scan_and_add(dict, comment_obj0)
            self.assertTrue(dict[message[1]].count > 0)

if __name__ == '__main__':
    unittest.main()