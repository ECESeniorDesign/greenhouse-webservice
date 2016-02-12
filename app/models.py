import datetime
import urllib2
import requests
import json
from config import PLANT_DATABASE, NUMBER_OF_PLANTS
import lazy_record
from lazy_record.validations import *
from lazy_record.associations import *

@has_one("plant_setting")
@has_many("sensor_data_points")
class Plant(lazy_record.Base):

    __attributes__ = {
        "name": str,
        "photo_url": str,
        "water_ideal": float,
        "water_tolerance": float,
        "light_ideal": float,
        "light_tolerance": float,
        "temperature_ideal": float,
        "temperature_tolerance": float,
        "acidity_ideal": float,
        "acidity_tolerance": float,
        "humidity_ideal": float,
        "humidity_tolerance": float,
        "mature_on": lazy_record.datetime,
        "slot_id": int,
        "plant_database_id": int,
    }

    __validates__ = {
        "slot_id": lambda record: unique(record, "slot_id") and \
                                  record.slot_id in
                                  range(1, NUMBER_OF_PLANTS + 1),
    }

    def record_sensor(self, sensor_name, sensor_value):
        points = getattr(self.sensor_data_points, sensor_name)()
        points.build(sensor_value=sensor_value).save()

    def __getattr__(self, attr):
        if attr in SensorDataPoint.SENSORS:
            # Asking for a sensor value
            point = getattr(self.sensor_data_points, attr)().last()
            if point:
                return point.sensor_value
            else:
                return 0
        else:
            return super(Plant, self).__getattr__(attr)

    class Mature(object):
        """Sentinel Object for Maturity of Mature Plants"""
        pass

    @property
    def mature_in(self):
        days = (self.mature_on - datetime.datetime.today()).days
        if days > 0:
            return days
        else:
            return Plant.Mature

    @property
    def mature(self):
        return self.mature_in == Plant.Mature

    @classmethod
    def for_slot(Plant, slot_id, raise_if_not_found=True):
        try:
            return Plant.find_by(slot_id=slot_id)
        except lazy_record.RecordNotFound:
            if raise_if_not_found:
                raise

    @classmethod
    def from_json(Plant, json_object):
        plant_database_id = json_object["id"]
        del json_object["id"]
        del json_object["inserted_at"]
        del json_object["updated_at"]
        plant = Plant(**json_object)
        plant.plant_database_id = plant_database_id
        plant.mature_on = datetime.datetime.today() + datetime.timedelta(
            json_object["maturity"])
        return plant

@belongs_to("plant")
class SensorDataPoint(lazy_record.Base):

    SENSORS = (
        "water",
        "light",
        "humidity",
        "acidity",
        "temperature",
    )

    __attributes__ = {
        "sensor_name": str,
        "sensor_value": float,
    }

    __scopes__ = {
        # lambda closures don't work in comprehensions, apparently...
        sensor: (lambda s: lambda query: query.where(sensor_name=s))(sensor)
        for sensor in SENSORS
    }

    __validates__ = {
        "sensor_name": lambda record: record.sensor_name in SensorDataPoint.SENSORS
    }

@has_many("notification_thresholds")
@belongs_to("plant")
class PlantSetting(lazy_record.Base):
    pass

@belongs_to("plant_setting")
class NotificationThreshold(lazy_record.Base):

    __attributes__ = {
        'sensor_name': str,
        'deviation_percent': int,
        'deviation_time': float,
        'triggered_at': lazy_record.datetime,
    }

    __validates__ = {
        "sensor_name": lambda record: record.sensor_name in SensorDataPoint.SENSORS,
        # Change to present when lazy_record is updated to 0.4.2 or 0.5.0
        'deviation_percent': lambda record: bool(record.deviation_percent),
        'deviation_time': lambda record: bool(record.deviation_time),
    }

    def __init__(self, *args, **kwargs):
        super(NotificationThreshold, self).__init__(*args, **kwargs)
        self.triggered_at = datetime.datetime.now()

    # lazy_record doesn't support through queries up a belongs_to
    @property
    def sensor_data_points(self):
        return self.plant.sensor_data_points.where(
            sensor_name=self.sensor_name)

    @property
    def plant(self):
        return self.plant_setting.plant

class PlantDatabase(object):

    class CannotConnect(Exception):
        """Exception for when the plant database cannot be found"""
        pass

    @classmethod
    def all_plants(PlantDatabase):
        try:
            response = urllib2.urlopen("http://{}/api/plants".format(
                PLANT_DATABASE))
            plant_list = json.load(response)
            plants = [Plant.from_json(plant) for plant in plant_list]
            return plants
        except urllib2.URLError:
            raise PlantDatabase.CannotConnect(PLANT_DATABASE)

    @classmethod
    def find_plant(PlantDatabase, id):
        try:
            response = urllib2.urlopen("http://{}/api/plants/{}".format(
                PLANT_DATABASE, id))
            plant = json.load(response)
            if plant:
                return Plant.from_json(plant)
            else:
                return None
        except urllib2.URLError:
            raise PlantDatabase.CannotConnect(PLANT_DATABASE)


class Token(lazy_record.Base):
    __attributes__ = {
        "token": str,
    }

    @classmethod
    def get(Token, token=None, **kwargs):
        if token:
            args = {'token': token}
        else:
            args = {'user': kwargs}
        try:
            response = requests.post("http://{}/api/token".format(
                                        PLANT_DATABASE),
                                    json=args)
            if response.ok:
                token = json.loads(response.text).get('token')
                Token.create(token=token)
            return response.ok
        except requests.exceptions.ConnectionError:
            raise PlantDatabase.CannotConnect(PLANT_DATABASE)

    @classmethod
    def refresh(Token):
        Token.get(token=Token.last().token)
