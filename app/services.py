import datetime
import requests
from config import PLANT_DATABASE

class Notifier(object):

    def __init__(self, threshold):
        self.threshold = threshold

    def notify(self):
        try:
            requests.post("http://{}/api/notify".format(PLANT_DATABASE),
                          data={'plant': self.threshold.plant.name})
        except requests.exceptions.ConnectionError:
            pass
        else:
            self.threshold.triggered_at = datetime.datetime.now()
            self.threshold.save()
