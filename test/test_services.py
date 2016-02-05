import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.services as services
from app.config import PLANT_DATABASE

@mock.patch("app.services.requests.post")
class TestNotifier(unittest.TestCase):

    def setUp(self):
        plant = mock.Mock(name="plant")
        plant.name = "Hydrangea"
        self.notification_threshold = mock.Mock(
            name="notification_threshold",
            plant=plant,
            save=mock.Mock(),
            triggered_at=dt(2011, 01, 1))
        self.notifier = services.Notifier(self.notification_threshold)

    @mock.patch("app.services.datetime.datetime")
    def test_sets_triggered_at_on_threshold(self, datetime, post):
        datetime.now.return_value = dt(2016, 02, 11)
        self.notifier.notify()
        self.assertEqual(self.notification_threshold.triggered_at,
                         dt(2016, 02, 11))
        self.notification_threshold.save.assert_called_with()

    def test_sends_notification(self, post):
        self.notifier.notify()
        post.assert_called_with(
            "http://{}/api/notify".format(PLANT_DATABASE),
            # later worry about having the correct headers
            data={'plant': 'Hydrangea'}
        )

    def test_does_not_set_triggered_if_notification_isnt_sent(self, post):
        post.side_effect = services.requests.exceptions.ConnectionError
        self.notifier.notify()
        self.assertEqual(self.notification_threshold.triggered_at,
                         dt(2011, 01, 1))
        self.notification_threshold.save.assert_not_called()

if __name__ == '__main__':
    unittest.main()
