import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.services as services
from app.config import PLANT_DATABASE

@mock.patch("app.services.requests")
class TestNotifier(unittest.TestCase):

    def setUp(self):
        plant = mock.Mock(name="plant")
        plant.name = "Hydrangea"
        self.notification_threshold = mock.Mock(
            name="notification_threshold",
            plant=plant,
            save=mock.Mock())
        self.notifier = services.Notifier(self.notification_threshold)

    @mock.patch("app.services.datetime.datetime")
    def test_sets_triggered_at_on_threshold(self, datetime, requests):
        datetime.now.return_value = dt(2016, 02, 11)
        self.notifier.notify()
        self.assertEqual(self.notification_threshold.triggered_at,
                         dt(2016, 02, 11))
        self.notification_threshold.save.assert_called_with()

    def test_sends_notification(self, requests):
        self.notifier.notify()
        requests.post.assert_called_with(
            "http://{}/api/notify".format(PLANT_DATABASE),
            # later worry about having the correct headers
            data={'plant': 'Hydrangea'}
        )

if __name__ == '__main__':
    unittest.main()
