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
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=50.0)]
        datetime.now.return_value = dt(2016, 01, 02, 12)
        self.policy.should_notify()
        self.notification_threshold\
            .sensor_data_points\
            .where.assert_has_calls([mock.call("created_at > ?",
                                          dt(2015, 05, 11)),
                                     mock.call("created_at > ?",
                                          dt(2016, 01, 02, 10, 45))])

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
            .where.side_effect = [[mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=50.0)],
                                  [mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0)]]
        self.assertTrue(self.policy.should_notify())

    def test_should_notify_when_above_tolerance(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.side_effect = [[mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=50.0)],
                                  [mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0)]]
        self.assertTrue(self.policy.should_notify())

    def test_should_notify_when_outside_tolerance(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.side_effect = [[mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=50.0)],
                                  [mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0)]]
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

    def test_should_not_notify_once_already_triggered(self):
        self.notification_threshold\
            .sensor_data_points\
            .where.return_value = [mock.Mock(name="sensor_data_point",
                                             sensor_value=17.0),
                                   mock.Mock(name="sensor_data_point",
                                             sensor_value=94.0)]
        self.assertFalse(self.policy.should_notify())


class TestTokenRefreshPolicy(unittest.TestCase):

    @mock.patch("app.models.Token")
    @mock.patch("app.policies.datetime.datetime")
    def test_required_when_older_than_12_hours(self, datetime, Token):
        datetime.today.return_value = dt(2016, 01, 01, 12, 01)
        Token.last.return_value = mock.Mock(created_at=dt(2016, 01, 01))
        self.assertTrue(policies.TokenRefreshPolicy().requires_refresh())

    @mock.patch("app.models.Token")
    @mock.patch("app.policies.datetime.datetime")
    def test_not_required_when_newer_than_12_hours(self, datetime, Token):
        datetime.today.return_value = dt(2016, 01, 01, 11, 59)
        Token.last.return_value = mock.Mock(created_at=dt(2016, 01, 01))
        self.assertFalse(policies.TokenRefreshPolicy().requires_refresh())

    @mock.patch("app.models.Token")
    @mock.patch("app.policies.datetime.datetime")
    def test_expired_when_older_than_1_day(self, datetime, Token):
        datetime.today.return_value = dt(2016, 01, 02, 01)
        Token.last.return_value = mock.Mock(created_at=dt(2016, 01, 01))
        self.assertTrue(policies.TokenRefreshPolicy().requires_authentication())

    @mock.patch("app.models.Token")
    @mock.patch("app.policies.datetime.datetime")
    def test_not_expired_when_newer_than_1_day(self, datetime, Token):
        datetime.today.return_value = dt(2016, 01, 01, 23, 59)
        Token.last.return_value = mock.Mock(created_at=dt(2016, 01, 01))
        self.assertFalse(policies.TokenRefreshPolicy().requires_authentication())

    @mock.patch("app.models.Token")
    @mock.patch("app.policies.datetime.datetime")
    def test_not_required_when_no_token(self, datetime, Token):
        datetime.today.return_value = dt(2016, 01, 01, 11, 59)
        Token.last.return_value = None
        self.assertFalse(policies.TokenRefreshPolicy().requires_refresh())

    @mock.patch("app.models.Token")
    @mock.patch("app.policies.datetime.datetime")
    def test_expired_when_no_token(self, datetime, Token):
        datetime.today.return_value = dt(2016, 01, 01, 23, 59)
        Token.last.return_value = None
        self.assertTrue(policies.TokenRefreshPolicy().requires_authentication())


class TestWaterNotificationPolicy(unittest.TestCase):

    def test_notification_required_when_water_level_low(self):
        water_level = mock.Mock(name="WaterLevel", level=12)
        self.assertTrue(policies.WaterNotificationPolicy(water_level
                               ).should_notify())

    def test_notification_not_required_when_water_level_high(self):
        water_level = mock.Mock(name="WaterLevel", level=87)
        self.assertFalse(policies.WaterNotificationPolicy(water_level
                               ).should_notify())

    def test_notification_not_required_when_no_water(self):
        self.assertFalse(policies.WaterNotificationPolicy(None
                               ).should_notify())


class TestIdealConditions(unittest.TestCase):

    def setUp(self):
        self.plant1 = plant()
        self.plant2 = plant()
        self.plant2.water_ideal = 72.0
        self.plant2.water_tolerance = 20.0
        self.conditions = policies.IdealConditions(self.plant1, self.plant2)

    def test_picks_ideal_as_weighted_average(self):
        self.assertEqual(self.conditions.ideal("water"), 66.0)

    def test_picks_ideal_with_disparate_plant_conditions(self):
        self.plant2.water_ideal = 185.0
        self.plant2.water_tolerance = 140.0
        self.assertEqual(self.conditions.ideal("water"), 79.59)

    def test_picks_ideal_with_tight_tolerances(self):
        self.plant2.water_ideal = 185.0
        self.plant2.water_tolerance = 128.5
        self.plant1.water_tolerance = 0.5
        self.assertEqual(self.conditions.ideal("water"), 57.5)

    def test_picks_padded_upper_if_possible(self):
        self.assertEqual(self.conditions.max("water"), 79.5)

    def test_uses_standard_upper_if_padding_fails(self):
        self.plant2.water_tolerance = 5.0
        self.plant2.water_ideal = 86.0
        self.assertEqual(self.conditions.max("water"), 87.0)

    def test_picks_padded_lower_if_possible(self):
        self.assertEqual(self.conditions.min("water"), 57.0)

    def test_uses_standard_lower_if_padding_fails(self):
        self.plant2.water_tolerance = 7.0
        self.plant2.water_ideal = 23.0
        self.assertEqual(self.conditions.min("water"), 27.0)

    def test_uses_default_window_if_cannot_pad(self):
        self.plant2.water_tolerance = 7.0
        self.plant2.water_ideal = 23.0
        self.assertEqual(self.conditions.min("water"), 27.0)
        self.assertEqual(self.conditions.max("water"), 30.0)
        assert self.conditions.min("water") < self.conditions.ideal("water")
        assert self.conditions.ideal("water") < self.conditions.max("water")

    def test_picks_ideal_for_light(self):
        self.assertEqual(self.conditions.ideal("light"), 50.0)

    def test_picks_min_for_light(self):
        self.assertEqual(self.conditions.min("light"), 42.5)

    def test_picks_max_for_light(self):
        self.assertEqual(self.conditions.max("light"), 57.5)

    def test_determines_if_near_ideal(self):
        # Upper bound for in range
        self.assertTrue(self.conditions.near_ideal("water", 72))
        # Lower bound in range
        self.assertTrue(self.conditions.near_ideal("water", 62))
        # Lower for out of range
        self.assertFalse(self.conditions.near_ideal("water", 73))
        # Upper for out of range
        self.assertFalse(self.conditions.near_ideal("water", 61))


class TestControlActivationPolicy(unittest.TestCase):

    def setUp(self):
        self.conditions = {
            "water": {"ideal": 51.0, "min": 21.0, "max": 71.0},
            "light": {"ideal": 51.0, "min": 21.0, "max": 71.0},
            "humidity": {"ideal": 51.0, "min": 21.0, "max": 71.0},
            "temperature": {"ideal": 51.0, "min": 21.0, "max": 71.0}
        }
        self.ideal_conditions = IdealConditionsStub(self.conditions)
        self.controls = {
            "light": mock.Mock(name="light_control", may_activate=True, active=False),
            "pump": mock.Mock(name="pump_control", may_activate=True, active=False),
            "fan": mock.Mock(name="fan_control", may_activate=True, active=False)
        }
        self.conditions = {
            "light": 15.0,
            "water": 15.0,
            "humidity": 15.0,
            "temperature": 15.0
        }
        self.policy = policies.ControlActivationPolicy(self.ideal_conditions,
                                                       self.conditions,
                                                       self.controls)

    def test_activates_lights_if_below_min(self):
        self.assertTrue(self.policy.should_activate("light"))

    def test_does_not_activate_lights_above_min(self):
        self.conditions["light"] = 25.0
        self.assertFalse(self.policy.should_activate("light"))

    def test_does_not_activate_lights_if_active(self):
        self.controls["light"].active = True
        self.assertFalse(self.policy.should_activate("light"))

    def test_does_not_activate_lights_if_may_not_activate(self):
        self.controls["light"].may_activate = False
        self.assertFalse(self.policy.should_activate("light"))

    def test_activates_fans_if_above_max(self):
        self.conditions["humidity"] = 75.0
        self.assertTrue(self.policy.should_activate("fan"))

    def test_does_not_activate_fans_below_max(self):
        self.assertFalse(self.policy.should_activate("fan"))

    def test_does_not_activate_fans_if_active(self):
        self.controls["fan"].active = True
        self.conditions["humidity"] = 75.0
        self.assertFalse(self.policy.should_activate("fan"))

    def test_does_not_activate_fan_if_may_not_activate(self):
        self.conditions["humidity"] = 75.0
        self.controls["fan"].may_activate = False
        self.assertFalse(self.policy.should_activate("fan"))

    def test_activates_pump_if_humid_and_water_below_min(self):
        self.assertTrue(self.policy.should_activate("pump"))

    def test_does_not_activate_pump_if_water_above_min(self):
        self.conditions["water"] = 25.0
        self.assertFalse(self.policy.should_activate("pump"))

    def test_does_not_activate_pump_if_humidity_above_min(self):
        self.conditions["humidity"] = 25.0
        self.assertFalse(self.policy.should_activate("pump"))

    def test_deactivates_lights_if_above_ideal(self):
        self.controls["light"].active = True
        self.conditions["light"] = 53.0
        self.assertTrue(self.policy.should_deactivate("light"))

    def test_does_not_deactivate_lights_below_ideal(self):
        self.controls["light"].active = True
        self.conditions["light"] = 50.0
        self.assertFalse(self.policy.should_deactivate("light"))

    def test_does_not_deactivate_lights_if_inactive(self):
        self.conditions["light"] = 53.0
        self.assertFalse(self.policy.should_deactivate("light"))

    def test_deactivates_lights_if_may_not_activate(self):
        self.controls["light"].active = True
        self.conditions["light"] = 53.0
        self.controls["light"].may_activate = False
        self.assertTrue(self.policy.should_deactivate("light"))

    def test_deactivates_fans_if_below_ideal(self):
        self.controls["fan"].active = True
        self.conditions["humidity"] = 50.0
        self.assertTrue(self.policy.should_deactivate("fan"))

    def test_does_not_deactivate_fans_above_ideal(self):
        self.controls["fan"].active = True
        self.conditions["humidity"] = 55.0
        self.assertFalse(self.policy.should_activate("fan"))

    def test_does_not_deactivate_fans_if_inactive(self):
        self.controls["fan"].active = False
        self.conditions["humidity"] = 50.0
        self.assertFalse(self.policy.should_activate("fan"))

    def test_deactivates_fan_if_may_not_activate(self):
        self.controls["fan"].active = True
        self.conditions["humidity"] = 50.0
        self.controls["fan"].may_activate = False
        self.assertTrue(self.policy.should_deactivate("fan"))

    def test_does_not_deactivates_pump_if_humid_and_water_below_ideal(self):
        self.controls["fan"].active = True
        self.assertFalse(self.policy.should_deactivate("pump"))

    def test_deactivates_pump_if_water_above_ideal(self):
        self.controls["fan"].active = True
        self.conditions["water"] = 55.0
        self.assertFalse(self.policy.should_deactivate("pump"))

    def test_deactivates_pump_if_humidity_above_ideal(self):
        self.controls["fan"].active = True
        self.conditions["humidity"] = 55.0
        self.assertFalse(self.policy.should_deactivate("pump"))

class IdealConditionsStub(object):

    def __init__(self, conditions):
        self.conditions = conditions

    def ideal(self, metric):
        return self.conditions[metric]["ideal"]

    def min(self, metric):
        return self.conditions[metric]["min"]

    def max(self, metric):
        return self.conditions[metric]["max"]


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
