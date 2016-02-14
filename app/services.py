import datetime
import requests
from config import PLANT_DATABASE
import models

class Notifier(object):

    class InvalidCredentials(object):
        pass

    def __init__(self, data, callback):
        self.data = dict(data)
        self.callback = callback

    def notify(self):
        self.data['token'] = models.Token.last().token
        try:
            response = requests.post("http://{}/api/notify".format(PLANT_DATABASE),
                                     data=self.data)
            if response.ok:
                self.callback()
            elif response.status_code == 403:
                return Notifier.InvalidCredentials
        except requests.exceptions.ConnectionError:
            pass

def PlantNotifier(threshold):
    def callback():
        threshold.triggered_at = datetime.datetime.now()
        threshold.save()
    return Notifier({'plant_name': threshold.plant.name}, callback)
