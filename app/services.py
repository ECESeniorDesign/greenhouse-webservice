import datetime
import requests
from config import PLANT_DATABASE
import models

class Notifier(object):

    class InvalidCredentials(object):
        pass

    def __init__(self, data, callback=lambda: None):
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
    return Notifier({'title': '"{}" needs attention!'.format(threshold.plant.name),
                     'message': ('Check up on your {} to ensure that '
                                'it is alright!').format(threshold.plant.name)
                     }, callback)

def WaterLevelNotifier(level):
    return Notifier({
        'title': "Water Level Low!",
        'message': "Please fill the greenhouse's water tank, it has only 12% remaining"
    })

class PlantUpdater(object):

    def __init__(self, plant):
        self.plant = plant

    def update(self):
        try:
            plant_data = models.PlantDatabase.plant_params(
                self.plant.plant_database_id,
                filter=['maturity'])
            self.plant.update(**plant_data)
            return True
        except:
            return False
