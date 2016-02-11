import datetime

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
