import datetime
import requests
from config import PLANT_DATABASE
import models

class Notifier(object):

    class InvalidCredentials(object):
        pass

    def __init__(self, threshold):
        self.threshold = threshold

    def notify(self):
        try:
            response = requests.post("http://{}/api/notify".format(PLANT_DATABASE),
                                     data={'plant_name': self.threshold.plant.name,
                                           'token': models.Token.last().token })
            if response.ok:
                self.threshold.triggered_at = datetime.datetime.now()
                self.threshold.save()
            elif response.status_code == 403:
                return Notifier.InvalidCredentials
        except requests.exceptions.ConnectionError:
            pass
