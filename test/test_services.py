import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.services as services
from app.config import PLANT_DATABASE
import app.models as models

@mock.patch("app.models.Token")
@mock.patch("app.services.requests.post")
class TestPlantNotifier(unittest.TestCase):

    def setUp(self):
        plant = mock.Mock(name="plant")
        plant.name = "Hydrangea"
        self.notification_threshold = mock.Mock(
            name="notification_threshold",
            plant=plant,
            save=mock.Mock(),
            triggered_at=dt(2011, 01, 1))
        self.notifier = services.PlantNotifier(self.notification_threshold)

    @mock.patch("app.services.datetime.datetime")
    def test_sets_triggered_at_on_threshold(self, datetime, post, Token):
        datetime.now.return_value = dt(2016, 02, 11)
        self.notifier.notify()
        self.assertEqual(self.notification_threshold.triggered_at,
                         dt(2016, 02, 11))
        self.notification_threshold.save.assert_called_with()

    def test_sends_notification(self, post, Token):
        self.notifier.notify()
        token = Token.last.return_value.token
        post.assert_called_with(
            "http://{}/api/notify".format(PLANT_DATABASE),
            data={'title': '"Hydrangea" needs attention!',
                  'message': 'Check up on your Hydrangea to ensure that it is alright!',
                  'token': token}
        )

    def test_does_not_set_triggered_if_notification_isnt_sent(self, post, Token):
        post.side_effect = services.requests.exceptions.ConnectionError
        self.notifier.notify()
        self.assertEqual(self.notification_threshold.triggered_at,
                         dt(2011, 01, 1))
        self.notification_threshold.save.assert_not_called()

    def test_does_not_set_triggered_if_invalid_credentials(self, post, Token):
        post.return_value = mock.Mock(ok=False, status_code=403)
        self.notifier.notify()
        self.assertEqual(self.notification_threshold.triggered_at,
                         dt(2011, 01, 1))
        self.notification_threshold.save.assert_not_called()

    def test_returns_if_invalid_credentials(self, post, Token):
        post.return_value = mock.Mock(ok=False, status_code=403)
        self.assertEqual(self.notifier.notify(),
                         services.Notifier.InvalidCredentials)


@mock.patch("app.models.Token")
@mock.patch("app.services.requests.post")
class TestWaterLevelNotifier(unittest.TestCase):

    def setUp(self):
        self.notifier = services.WaterLevelNotifier(12)

    def test_sends_notification(self, post, Token):
        self.notifier.notify()
        token = Token.last.return_value.token
        post.assert_called_with(
            "http://{}/api/notify".format(PLANT_DATABASE),
            data={'title': 'Water Level Low!',
                  'message': 'Please fill the greenhouse\'s water tank, it has only 12% remaining',
                  'token': token}
        )

    def test_returns_if_invalid_credentials(self, post, Token):
        post.return_value = mock.Mock(ok=False, status_code=403)
        self.assertEqual(self.notifier.notify(),
                         services.Notifier.InvalidCredentials)


@mock.patch("app.models.PlantDatabase.plant_params")
class TestPlantUpdater(unittest.TestCase):

    def setUp(self):
        self.plant = mock.Mock(name="plant", plant_database_id=11)
        self.updater = services.PlantUpdater(self.plant)

    def test_gets_plant_data(self, plant_params):
        self.updater.update()
        plant_params.assert_called_with(11, filter=["maturity"])

    def test_returns_false_if_cannot_connect(self, plant_params):
        plant_params.side_effect = models.PlantDatabase.CannotConnect("PLANT_DATABASE")
        self.assertEqual(self.updater.update(), False)

    def test_updates_plant_with_data(self, plant_params):
        plant_data = {
            "water_tolerance": 30.0,
            "water_ideal": 57.0,
            "photo_url": "testPlant.png",
            "name": "testPlant",
            "light_tolerance": 10.0,
            "light_ideal": 50.0,
            "plant_database_id": 1,
            "humidity_tolerance": 0.01,
            "humidity_ideal": 0.2,
            "acidity_tolerance": 1.0,
            "acidity_ideal": 9.0
        }
        plant_params.return_value = plant_data
        self.updater.update()
        self.plant.update.assert_called_with(**plant_data)

    def test_returns_true_on_success(self, plant_params):
        self.assertEqual(self.updater.update(), True)


if __name__ == '__main__':
    unittest.main()
