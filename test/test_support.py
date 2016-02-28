import unittest
import mock
import os
import sys
from datetime import datetime, time
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.support as support

class TestTimeType(unittest.TestCase):

    def test_casts_datetime_to_time(self):
        self.assertEqual(support.time(datetime(2015, 01, 12, 04, 15, 11)),
                         time(4, 15, 11))

    def test_casts_time_to_time(self):
        self.assertEqual(support.time(time(5, 4, 11)), time(5, 4, 11))


if __name__ == '__main__':
    unittest.main()
