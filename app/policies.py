import datetime
import models

class NotificationPolicy(object):

    def __init__(self, notification_threshold):
        self.notification_threshold = notification_threshold

    def relevant_points(self):
        hour_delta = int(self.notification_threshold.deviation_time)
        minute_delta = (self.notification_threshold.deviation_time % 1) * 60
        return self.notification_threshold\
                   .sensor_data_points\
                   .where("created_at > ?",
                          datetime.datetime.now() - datetime.timedelta(
                              hours=hour_delta, minutes=minute_delta))

    def _get_metric(self, kind):
        return getattr(self.notification_threshold.plant,
                               self.notification_threshold.sensor_name + \
                               "_{}".format(kind))

    def thresholds(self):
        ideal_metric = self._get_metric("ideal")
        tolerance_metric = self._get_metric("tolerance")
        allowed_difference = float(
            self.notification_threshold.deviation_percent)/100.0
        low_threshold = (ideal_metric - tolerance_metric) * \
                        (1 - allowed_difference)
        high_threshold = (ideal_metric + tolerance_metric) * \
                         (1 + allowed_difference)
        return low_threshold, high_threshold

    def already_triggered(self):
        low_threshold, high_threshold = self.thresholds()
        points = self.notification_threshold\
                     .sensor_data_points\
                     .where("created_at > ?",
                            self.notification_threshold.triggered_at)
        return all(p.sensor_value > high_threshold or
                   p.sensor_value < low_threshold for
                   p in points)

    def should_notify(self):
        low_threshold, high_threshold = self.thresholds()
        return not self.already_triggered() and \
               all(p.sensor_value > high_threshold or
                   p.sensor_value < low_threshold for
                   p in self.relevant_points())

class TokenRefreshPolicy(object):

    def _token_older_than(self, if_none=False, **kwargs):
        if models.Token.last():
            return (models.Token.last().created_at + \
                    datetime.timedelta(**kwargs)) < datetime.datetime.today()
        else:
            return if_none

    def requires_refresh(self):
        return self._token_older_than(hours=12, if_none=False)

    def requires_authentication(self):
        return self._token_older_than(days=1, if_none=True)

class WaterNotificationPolicy(object):

    def __init__(self, water_level):
        self.water_level = water_level

    def should_notify(self):
        if self.water_level:
            return self.water_level.level < 15
        else:
            return False

class IdealConditions(object):

    def __init__(self, *plants):
        self.plants = plants

    def ideal(self, metric):
        """Returns the ideal +metric+ value for the plants"""
        weighted_sum = sum(self._ideal_value(plant, metric) / \
                           self._tolerance_value(plant, metric)
                           for plant in self.plants)
        weights = sum(1./self._tolerance_value(plant, metric)
                      for plant in self.plants)
        return round(weighted_sum / weights, 2)

    def max(self, metric):
        """Returns the max +metric+ value for the plants"""
        if self._cannot_pad(metric):
            return self._absolute_max(metric)
        else:
            return self._padded_max(metric)

    def min(self, metric):
        """Returns the min +metric+ value for the plants"""
        if self._cannot_pad(metric):
            return self._absolute_min(metric)
        else:
            return self._padded_min(metric)

    # Private methods

    def _ideal_value(self, plant, metric):
        return getattr(plant, metric + "_ideal")

    def _tolerance_value(self, plant, metric):
        return getattr(plant, metric + "_tolerance")

    def _absolute_min(self, metric):
        return max(self._ideal_value(plant, metric) - \
                   self._tolerance_value(plant, metric)
                   for plant in self.plants)

    def _padded_min(self, metric):
        def ideal_minus_tolerance(plant):
            return self._ideal_value(plant, metric) - \
                   self._tolerance_value(plant, metric)

        highest = max(self.plants, key=ideal_minus_tolerance)
        return self._ideal_value(highest, metric) - \
               0.75 * self._tolerance_value(highest, metric)

    def _padded_max(self, metric):
        def ideal_plus_tolerance(plant):
            return self._ideal_value(plant, metric) + \
                   self._tolerance_value(plant, metric)

        lowest = min(self.plants, key=ideal_plus_tolerance)
        return self._ideal_value(lowest, metric) + \
               0.75 * self._tolerance_value(lowest, metric)

    def _absolute_max(self, metric):
        return min(self._ideal_value(plant, metric) + \
                   self._tolerance_value(plant, metric)
                   for plant in self.plants)

    def _cannot_pad(self, metric):
        return (self._padded_max(metric) < self._absolute_min(metric)) or \
               (self._padded_min(metric) > self._absolute_max(metric)) or \
               (self._padded_min(metric) > self.ideal(metric)) or \
               (self._padded_max(metric) < self.ideal(metric))
