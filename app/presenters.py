import models
import re
from datetime import datetime

class PlantPresenter(object):

    def __init__(self, plant):
        self.plant = plant

    def formatted_value(self, metric):
        if metric == "humidity":
            return "{0:0.1%}".format(getattr(self.plant, metric))
        else:
            return getattr(self.plant, metric)

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
