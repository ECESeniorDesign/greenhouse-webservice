import datetime
import requests
from config import PLANT_DATABASE
import models
from greenhouse_envmgmt.control import ControlCluster
try:
    # This will fail on systems without linux/types.h
    import smbus
    from greenhouse_envmgmt.sense import SensorCluster
    ControlCluster.bus = smbus.SMBus(1)
    SensorCluster.bus = ControlCluster.bus
except:
    # HACK so that SensorCluster is defined when the above import fails
    # this is to allow automated testing even when smbus cannot be installed
    SensorCluster = None

class Notifier(object):

    class InvalidCredentials(object):
        pass

    def __init__(self, data, callback=lambda: None):
        self.data = dict(data)
        self.callback = callback

    def notify(self):
        token = models.Token.last()
        if token:
            self.data['token'] = token.token
        else:
            return
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
    plant = threshold.plant
    sensor = threshold.sensor_name
    ideal = getattr(plant, sensor + "_ideal")
    current = threshold.sensor_data_points.last().sensor_value
    if current > ideal:
        status = "high"
    else:
        status = "low"
    return Notifier({'title': '"{}" {} {}!'.format(plant.name, sensor, status),
                     'message': 'Your {}\'s {} is {} ({}). It should be {}'.format(
                                    plant.name, sensor, status, current, ideal)
                     }, callback)

def WaterLevelNotifier(level):
    return Notifier({
        'title': "Greenhouse Water Level Low!",
        'message': "Please fill the greenhouse's water tank, it has only {}% remaining".format(level)
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

class Control(object):
    """Wrapper for greenhouse_envmgmt Control API"""

    cluster = ControlCluster(1)

    def __init__(self, name):
        self.name = name

    def on(self):
        Control.cluster.control(on=self.name)

    def off(self):
        Control.cluster.control(off=self.name)

class Sensor(object):
    """Wrapper for greenhouse_envmgmt Sensor API"""

    def __init__(self, plant):
        self.plant = plant

    def get_values(self):
        cluster = SensorCluster(ID=self.plant.slot_id)
        values = cluster.sensor_values()
        for sensor, value in values.items():
            self.plant.record_sensor(sensor, value)

    @classmethod
    def get_water_level(cls):
        level = SensorCluster.get_water_level()
        models.WaterLevel.create(level=level*100)
