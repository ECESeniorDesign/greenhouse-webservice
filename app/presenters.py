import models
import re
from datetime import datetime

class PlantPresenter(object):

    def __init__(self, plant):
        self.plant = plant

    def formatted_value(self, metric):
        value = getattr(self.plant, metric)
        if metric == "humidity":
            return "{0:0.1%}".format(value)
        elif metric == "temperature":
            return "{0:0.1f}&deg;F".format(value)
        else:
            return "{0:0.1f}".format(value)

    @property
    def maturity_dial_min(self):
        total = (self.plant.mature_on - self.plant.created_at).days
        remaining = self.plant.mature_in
        return 2*remaining - total

    @property
    def maturity_dial_max(self):
        return 2 * self.plant.mature_in

    def _within_tolerance(self, ideal, current, tolerance):
        lower_limit = ideal - tolerance
        upper_limit = ideal + tolerance
        return lower_limit < current < upper_limit

    def bar_width(self, metric):
        return self._bar_width(*self._get_params(metric))

    def error_bar_width(self, metric):
        return self._error_bar_width(*self._get_params(metric))

    def within_tolerance(self, metric):
        return self._within_tolerance(*self._get_params(metric))

    def over_ideal(self, metric):
        ideal, current, tolerance = self._get_params(metric)
        return current > ideal

    def icon_for(self, metric):
        icons = {
            "light": "fa fa-sun-o",
            "water": "wi wi-raindrop",
        }
        return icons.get(metric, "")

    def bar_class(self, metric):
        classes = {
            "light": "progress-bar-sun",
            "water": "progress-bar-water",
        }
        return classes.get(metric, "")

    def __getattr__(self, attr):
        return getattr(self.plant, attr)

    def _bar_width(self, ideal, current, tolerance):
        if current > ideal + tolerance:
            return ideal + tolerance
        else:
            return current

    def _error_bar_width(self, ideal, current, tolerance):
        upper_limit = ideal + tolerance
        if current > upper_limit:
            return min(current - upper_limit, 100 - upper_limit)
        elif current < ideal - tolerance:
            return ideal - (current + tolerance)
        else:
            return 0.0

    def _get_params(self, metric):
        # normalize values so that ideal is 50%
        current = getattr(self.plant, metric)
        ideal = getattr(self.plant, metric + "_ideal")
        tolerance = getattr(self.plant, metric + "_tolerance")
        normalized_current = ((current * 50.0) / ideal)
        # TODO normalize so that the tolerance bands are at 20% & 80%
        normalized_tolerance = ((tolerance * 50.0) / ideal)
        normalized_ideal = 50.0
        return normalized_ideal, normalized_current, normalized_tolerance

class ChartDataPresenter(object):

    formats = {
        "light": {
            "color": "#FDB45C",
            "highlight": "#FFC870",
        },
        "water": {
            "color": "#0198E1",
            "highlight": "#42C0FB",
        },
        "humidity": {
            "color": "#949FB1",
            "highlight": "#A8B3C5",
        },
        "temperature": {
            "color": "#F7464A",
            "highlight": "#FF5A5E",
        },
        "acidity": {
            "color": "#46BFBD",
            "highlight": "#5AD3D1",
        },
        "default": {
            "color": "#949FB1",
            "highlight": "#A8B3C5",
        }
    }

    def __init__(self, plant):
        self.plant = plant

    def ideal_chart_data(self):
        def sensor_data_for(sensor):
            ideal_points = getattr(self.plant.sensor_data_points, sensor)()
            points = getattr(self.plant.sensor_data_points, sensor)()
            ideal = getattr(self.plant, "{}_ideal".format(sensor))
            tolerance = getattr(self.plant, "{}_tolerance".format(sensor))
            within_tolerance_count = len(ideal_points.where(
                "sensor_value >= ? AND sensor_value <= ?",
                ideal - tolerance,
                ideal + tolerance))
            total_count = len(points)
            colors = ChartDataPresenter.formats.get(sensor,
                ChartDataPresenter.formats["default"])
            if total_count > 0:
                percent_within_tolerance = int(
                    round(float(within_tolerance_count) * 100.0 / total_count))
            else:
                percent_within_tolerance = 0
            return {
                "label": sensor.title(),
                "value": percent_within_tolerance,
                "color": colors["color"],
                "highlight": colors["highlight"],
            }
        return [sensor_data_for(sensor) for sensor in models.SensorDataPoint.SENSORS]

    def history_chart_data_for(self, sensor):
        # For some reason, it is getting 2 new points per cycle
        num_points = 8
        points = getattr(self.plant.sensor_data_points, sensor)()
        data = [point.sensor_value for point in points][-num_points:]
        return  {
                    "labels": [""] * num_points,
                    "datasets": [
                                    {
                                        'fillColor': "rgba(220,220,220,0.2)",
                                        'strokeColor': "rgba(220,220,220,1)",
                                        'pointColor': "rgba(220,220,220,1)",
                                        'pointStrokeColor': "#fff",
                                        'data': data,
                                    }
                                ]
                }
