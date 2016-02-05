import datetime
import requests
from config import PLANT_DATABASE

class Notifier(object):

    def __init__(self, threshold):
        self.threshold = threshold

    def notify(self):
        self.threshold.triggered_at = datetime.datetime.now()
        requests.post("http://{}/api/notify".format(PLANT_DATABASE),
                      data={'plant': self.threshold.plant.name})
        self.threshold.save()
