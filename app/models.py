import datetime
import urllib2
import requests
import json
from config import PLANT_DATABASE, NUMBER_OF_PLANTS
import lazy_record
from lazy_record.validations import *
from lazy_record.associations import *
import support
import services

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
        plant = Plant(**json_object)
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
    def _filter_params(PlantDatabase, params, filter=[]):
        params = dict(params)
        params["plant_database_id"] = params["id"]
        filter += ["id", "inserted_at", "updated_at"]
        return { k : v for k, v in params.items()
                 if k not in filter }

    @classmethod
    def _get_response(PlantDatabase, url):
        try:
            response = urllib2.urlopen("http://{}/api/{}".format(
                PLANT_DATABASE, url))
            return json.load(response)
        except urllib2.URLError:
            raise PlantDatabase.CannotConnect(PLANT_DATABASE)

    @classmethod
    def _process_list(PlantDatabase, plant_list):
        plant_args = (PlantDatabase._filter_params(params)
                      for params in plant_list)
        return [Plant.from_json(params) for params in plant_args]

    @classmethod
    def all_plants(PlantDatabase):
        response = PlantDatabase._get_response("plants")
        return PlantDatabase._process_list(response)

    @classmethod
    def find_plant(PlantDatabase, id):
        plant_params = PlantDatabase.plant_params(id)
        if plant_params:
            return Plant.from_json(plant_params)
        else:
            return None

    @classmethod
    def compatible_plants(PlantDatabase, plants):
        try:
            args = {"ids": [plant.plant_database_id for plant in plants]}
            response = requests.post("http://{}/api/plants/compatible".format(
                                        PLANT_DATABASE),
                                    json=args)
            plant_list = json.loads(response.content)
            return PlantDatabase._process_list(plant_list)
        except requests.exceptions.ConnectionError:
            raise PlantDatabase.CannotConnect(PLANT_DATABASE)

    @classmethod
    def plant_params(PlantDatabase, id, filter=[]):
        response = PlantDatabase._get_response("plants/{}".format(id))
        if response:
            return PlantDatabase._filter_params(response, filter)
        else:
            return None


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


class WaterLevel(lazy_record.Base):
    __attributes__ = {
        "level": int,
    }


class GlobalSetting(object):

    class __metaclass__(type):

        @property
        def controls(cls):
            return Control.all()

        @property
        def enabled_controls(cls):
            return Control.where(enabled=True)

        def control(cls, control):
            try:
                return Control.find_by(name=control)
            except lazy_record.RecordNotFound:
                return None

class Control(lazy_record.Base):

    class Always(object):
        pass

    class TemporarilyDisabled(object):
        pass

    __attributes__ = {
        'enabled': bool,
        'name': str,
        'active': bool,
        'disabled_at': lazy_record.datetime,
        'active_start': lazy_record.datetime,
        'active_end': lazy_record.datetime,
    }

    @property
    def enabled(self):
        if self._enabled and self.disabled_at is not None:
            threshold = datetime.datetime.now() - \
                        datetime.timedelta(minutes=15)
            if threshold > self.disabled_at:
                return True
            else:
                return Control.TemporarilyDisabled
        else:
            return bool(self._enabled)

    @property
    def active_during(self):
        period = (self.active_start, self.active_end)
        if None in period:
            return Control.Always
        return period

    @property
    def active_start(self):
        if self._active_end is None:
            return None
        return support.time(self._active_start)

    @property
    def active_end(self):
        if self._active_start is None:
            return None
        return support.time(self._active_end)

    @property
    def active_start_time(self):
        if self.active_start is None:
            return ''
        return self.active_start.strftime("%I:%M %p")

    @property
    def active_end_time(self):
        if self.active_end is None:
            return ''
        return self.active_end.strftime("%I:%M %p")

    def activate(self):
        self.disabled_at = None
        self.active = True
        services.Control(self.name).on()
        self.save()

    def deactivate(self):
        self.active = False
        services.Control(self.name).off()
        self.save()

    def _set_time(self, attr, value):
        if value is not None:
            dummy_datetime = datetime.datetime.combine(datetime.date.today(),
                                                       value)
        else:
            dummy_datetime = None
        setattr(self, "_" + attr, dummy_datetime)

    def __setattr__(self, attr, value):
        if attr in ('active_start', 'active_end'):
            self._set_time(attr, value)
        else:
            super(Control, self).__setattr__(attr, value)

    def temporarily_disable(self):
        self.disabled_at = datetime.datetime.now()
        self.deactivate()

    @property
    def may_activate(self):
        # Cannot activate if not currently enabled
        if self.enabled in (False, Control.TemporarilyDisabled):
            return False
        # Time window isn't an issue if it has no restriction
        if self.active_during is Control.Always:
            return True
        # Is is within the time window?
        after_start = self.active_start < datetime.datetime.now().time()
        before_end = datetime.datetime.now().time() < self.active_end
        # Do we want it within the time window (if end is before start,
        # then we want it outside the window)
        if self.active_start < self.active_end:
            return after_start and before_end
        else:
            return after_start or before_end
