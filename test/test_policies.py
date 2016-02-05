import unittest
import mock
import os
import sys
from datetime import datetime as dt
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import app.policies as policies

class TestNotificationPolicy(unittest.TestCase):
    def setUp(self):
        self.notification_threshold = notification_threshold()
        self.policy = policies.NotificationPolicy(self.notification_threshold)

    @mock.patch("app.policies.datetime.datetime")
    def test_queries_for_records(self, datetime):
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = []
        datetime.now.return_value = dt(2016, 01, 02, 12)
        self.policy.should_notify()
        self.notification_threshold\
            .sensor_data_points\
            .where.assert_called_with("created_at > ? AND created_at > ?",
                                      dt(2015, 05, 11),
                                      dt(2016, 01, 02, 10, 45))

    def test_should_not_notify_when_all_within_tolerance(self):
        # Hi/Lo = 93/18
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=18.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=93.0)]
        self.assertFalse(self.policy.should_notify())

    def test_should_notify_when_beneath_tolerance(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0)]
        self.assertTrue(self.policy.should_notify())

    def test_should_notify_when_above_tolerance(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0)]
        self.assertTrue(self.policy.should_notify())

    def test_should_notify_when_outside_tolerance(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0)]
        self.assertTrue(self.policy.should_notify())

    def test_should_not_notify_when_one_inside_tolerance(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=21.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0)]
        self.assertFalse(self.policy.should_notify())


def sensor_data_points():
    return mock.Mock(name="lazy_record.Query")

def plant():
    fixture = mock.Mock(name="Plant",
                        photo_url="testPlant.png",
                        water_ideal=57.0,
                        water_tolerance=30.0,
                        light_ideal=50.0,
                        light_tolerance=10.0,
                        acidity_ideal=9.0,
                        acidity_tolerance=1.0,
                        humidity_ideal=0.2,
                        humidity_tolerance=0.1,
                        mature_on=dt(2016, 1, 10),
                        slot_id=1,
                        plant_database_id=1,
                        sensor_data_points=sensor_data_points())
    fixture.name = "TestPlant"
    return fixture

def notification_threshold():
    p = plant()
    sdp = sensor_data_points()
    p.sensor_data_points = sdp
    fixture = mock.Mock(name="NotificationThreshold",
                        sensor_name="light",
                        deviation_time=1.25,
                        deviation_percent=55,
                        triggered_at=dt(2015, 05, 11),
                        sensor_data_points=sdp,
                        plant=p)
    return fixture

if __name__ == '__main__':
    unittest.main()