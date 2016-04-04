import flask
import models
import forms
import router
import config
import eventlet
import json
eventlet.monkey_patch()
from flask_socketio import SocketIO
import jinja2
import os
import presenters
import policies
import services
import datetime
from task_runner import BackgroundTaskRunner

template_dir = os.path.join(os.path.dirname(__file__), "templates")
loader = jinja2.FileSystemLoader(template_dir)
environment = jinja2.Environment(loader=loader)

app = flask.Flask(__name__)

from werkzeug import url_decode

class MethodRewriteMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'METHOD_OVERRIDE' in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get('__METHOD_OVERRIDE__')
            if method:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method
        return self.app(environ, start_response)

app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

socketio = SocketIO(app, async_mode='eventlet')
app.secret_key = config.SECRET_KEY
router = router.Router(app)
background = BackgroundTaskRunner(refresh=10)
daily = BackgroundTaskRunner(refresh=24 * 3600)

# Routing & Controllers

@router.route("/plants", exclude=["edit", "update"])
class PlantsController(object):
    
    @staticmethod
    def index():
        plants = [(models.Plant.for_slot(slot_id, False), slot_id)
                  for slot_id in range(1, config.NUMBER_OF_PLANTS + 1)]
        water_level = models.WaterLevel.last()
        if water_level:
            water = water_level.level
        else:
            water = 0
        return flask.render_template("plants/index.html",
                                     plants=plants,
                                     water=water)

    @staticmethod
    def new():
        current_plants = list(models.Plant.all())
        plants = models.PlantDatabase.compatible_plants(current_plants)
        slot_id = int(flask.request.args.get("slot_id"))
        return flask.render_template("plants/new.html",
                                     plants=plants,
                                     slot_id=slot_id)

    @staticmethod
    def create():
        plant = models.PlantDatabase.find_plant(
                    flask.request.form["plant_database_id"])
        if plant is None:
            flask.flash("Plant does not exist.", 'error')
            return flask.redirect(flask.url_for("PlantsController.index"))
        try:
            plant.update(slot_id=flask.request.form["slot_id"])
            plant.plant_setting = models.PlantSetting()
            plant.save()
            flask.flash("'{}' successfully added.".format(plant.name), 'notice')
            return flask.redirect(flask.url_for('PlantsController.show',
                                                id=plant.slot_id))
        except models.lazy_record.RecordInvalid:
            flask.flash("Could not add plant.", 'error')
            return flask.redirect(flask.url_for('PlantsController.index'))

    @staticmethod
    def show(id):
        plant = models.Plant.for_slot(id)
        presenter = presenters.PlantPresenter(plant)
        return flask.render_template("plants/show.html",
                                     plant=presenter)

    @staticmethod
    def destroy(id):
        plant = models.Plant.for_slot(id)
        plant.destroy()
        return flask.redirect(flask.url_for('PlantsController.index'))

@router.route("/plants/<plant_id>/logs", only=["index"])
class LogsController(object):

    @staticmethod
    def index(plant_id):
        plant = models.Plant.for_slot(plant_id)
        return flask.render_template("logs/index.html",
                                     plant=plant,
                                     sensors=list(
                                             enumerate(models.SensorDataPoint\
                                                             .SENSORS)))

    @router.endpoint("download")
    def download(plant_id):
        plant = models.Plant.for_slot(plant_id)
        presenter = presenters.LogDataPresenter(plant)
        response = flask.Response(presenter.log_string(), mimetype="text/plain")
        response.headers["Content-Disposition"] = 'attachment; filename=sensors.log'
        return response

@router.route("/plants/<plant_id>/settings", only=["index", "create"])
class PlantSettingsController(object):

    @staticmethod
    def index(plant_id):
        plant = models.Plant.for_slot(plant_id)
        settings = plant.plant_setting.notification_thresholds
        return flask.render_template("plant_settings/index.html",
                                     thresholds=settings,
                                     plant=plant,
                                     names=models.SensorDataPoint.SENSORS)

    @staticmethod
    def create(plant_id):
        plant = models.Plant.for_slot(plant_id)
        setting = plant.plant_setting
        thresholds = setting.notification_thresholds
        form = flask.request.form
        # Delete
        ids_to_delete = list(PlantSettingsController.deleted_thresholds(form))
        if ids_to_delete:
            for threshold in thresholds.where(id=ids_to_delete):
                threshold.destroy()
        failures = 0
        # Create
        for kw in PlantSettingsController.new_thresholds(form):
            try:
                thresholds.create(**kw)
            except models.lazy_record.RecordInvalid:
                failures += 1
        # Update
        for id, kw in PlantSettingsController.old_thresholds(form):
            threshold = thresholds.where(id=id).first()
            threshold.update(**kw)
            try:
                threshold.save()
            except models.lazy_record.RecordInvalid:
                failures += 1
        some_succeeded = \
            len(list(PlantSettingsController.all_thresholds(form))) > 0 and \
            len(list(PlantSettingsController.all_thresholds(form))) > failures

        if PlantSettingsController.form_valid(form) and not failures:
            flask.flash("Settings Updated", 'notice')
        elif some_succeeded:
            flask.flash("Some Settings Updated", 'warning')
        else:
            flask.flash("Settings could not be updated", 'error')
        return flask.redirect(flask.url_for('PlantSettingsController.index',
                                            plant_id=plant_id))

    @staticmethod
    def new_thresholds(form):
        for attr, percent, time, thresh_id, deleted in \
                PlantSettingsController.all_thresholds(form):
            if thresh_id == "":
                # New record
                yield {
                    'sensor_name': str(attr),
                    'deviation_percent': int(float(percent)),
                    'deviation_time': float(time),
                }

    @staticmethod
    def all_thresholds(form):
        thresholds = zip(form.getlist("attribute"),
                         form.getlist("deviation_percent"),
                         form.getlist("deviation_time"),
                         form.getlist("threshold_id"),
                         form.getlist("delete"))
        for attr, percent, time, thresh_id, deleted in thresholds:
            if "" in (attr, percent, time) or deleted != "false":
                continue
            yield attr, percent, time, thresh_id, deleted

    @staticmethod
    def old_thresholds(form):
        for attr, percent, time, thresh_id, deleted in \
                PlantSettingsController.all_thresholds(form):
            if thresh_id != "":
                # Old record
                yield int(thresh_id), {
                    'sensor_name': str(attr),
                    'deviation_percent': int(float(percent)),
                    'deviation_time': float(time),
                }

    @staticmethod
    def deleted_thresholds(form):
        thresholds = zip(form.getlist("attribute"),
                         form.getlist("deviation_percent"),
                         form.getlist("deviation_time"),
                         form.getlist("threshold_id"),
                         form.getlist("delete"))
        for attr, percent, time, thresh_id, deleted in thresholds:
            if deleted != "false" and thresh_id != "":
                # Existing record
                yield int(thresh_id)

    @staticmethod
    def form_valid(form):
        all_thresholds = zip(form.getlist("attribute"),
                             form.getlist("deviation_percent"),
                             form.getlist("deviation_time"),
                             form.getlist("threshold_id"),
                             form.getlist("delete"))
        for attr, percent, time, thresh_id, deleted in all_thresholds:
            if deleted != "false":
                continue
            if "" in (attr, percent, time) and not (attr == percent == time):
                return False
        return True

@router.route("/settings", only=["index", "create"])
class GlobalSettingsController(object):

    @staticmethod
    def index():
        controls = models.GlobalSetting.controls
        ns = models.PlantDatabase.get_notification_settings()
        notify_plants = models.GlobalSetting.notify_plants
        notify_maintenance = models.GlobalSetting.notify_maintenance
        return flask.render_template("global_settings/index.html",
                                     controls=controls,
                                     notification_settings=ns,
                                     notify_plants=notify_plants,
                                     notify_maintenance=notify_maintenance)

    @staticmethod
    def create():
        controls = models.GlobalSetting.controls
        form = forms.GlobalSettingsForm(controls, flask.request.form)
        form.submit()
        return flask.redirect(flask.url_for('PlantsController.index'))

@app.route("/login", methods=["GET"])
def login_page():
    return flask.render_template("sessions/new.html")

@app.route("/login", methods=["POST"])
def login():
    form = flask.request.form
    if models.Token.get(username=form.get("username", ""),
                        password=form.get("password", "")):
        return flask.redirect(flask.url_for('PlantsController.index'))
    else:
        flask.flash("Invalid Credentials", "error")
        return flask.render_template("sessions/new.html")

router.root(PlantsController, "index")

# API

@router.route("/api/plants", only=["index", "show", "create", "destroy"])
class APIPlantsController(object):

    @staticmethod
    def index():

        def present(plant):
            return presenters.APIPlantPresenter(plant).short_info()

        water = models.WaterLevel.last()
        if water:
            level = water.level
        else:
            level = 0
        plants = [present(plant) for plant in models.Plant.all()]
        return flask.jsonify({'plants': plants, 'water_level': level})

    @staticmethod
    def show(id):
        plant = models.Plant.for_slot(id, raise_if_not_found=False)
        return flask.jsonify(presenters.APIPlantPresenter(plant).long_info())

    @staticmethod
    def create():
        params = json.loads(flask.request.data)
        plant_database_id = params["plant_database_id"]
        slot_id = params["slot_id"]
        plant = models.PlantDatabase.find_plant(plant_database_id)
        if plant:
            plant.slot_id = slot_id
            plant.plant_setting = models.PlantSetting()
            plant.save()
            return flask.jsonify(presenters.APIPlantPresenter(plant).long_info())
        else:
            return flask.jsonify({'error': 'could not save plant'})

    @staticmethod
    def destroy(id):
        try:
            plant = models.Plant.for_slot(id)
            plant.destroy()
            return ('', 204)
        except models.lazy_record.RecordNotFound:
            return ('Plant not found', 404)

@router.route("/api/plants/<plant_id>/settings", only=["index", "create", "update", "destroy"])
class APIPlantSettingsController(object):

    @staticmethod
    def index(plant_id):
        plant = models.Plant.for_slot(plant_id, False)
        if plant:
            response = {'settings': []}
            for threshold in plant.plant_setting.notification_thresholds:
                response['settings'].append({
                    'id': threshold.id,
                    'sensor_name': threshold.sensor_name,
                    'deviation_percent': threshold.deviation_percent,
                    'deviation_time': threshold.deviation_time
                })
            return flask.jsonify(response)
        else:
            return flask.jsonify({"error": "plant not found"})

    @staticmethod
    def create(plant_id):
        params = json.loads(flask.request.data)
        threshold_params = {
            'sensor_name': params['sensor_name'],
            'deviation_percent': params['deviation_percent'],
            'deviation_time': params['deviation_time']
        }
        row = params['row']
        plant = models.Plant.for_slot(plant_id, False)
        if plant:
            setting = plant.plant_setting.notification_thresholds.create(
                **threshold_params)
            return flask.jsonify(dict(row=row, id=setting.id, **threshold_params))
        else:
            return flask.jsonify({"error": "plant not found"})

    @staticmethod
    def update(plant_id, id):
        params = json.loads(flask.request.data)
        threshold_params = {
            'sensor_name': params['sensor_name'],
            'deviation_percent': params['deviation_percent'],
            'deviation_time': params['deviation_time']
        }
        row = params['row']
        try:
            setting = models.NotificationThreshold.find(id)
            setting.update(**threshold_params)
            setting.save()
            return flask.jsonify(dict(row=row, **threshold_params))
        except models.lazy_record.RecordNotFound:
            return flask.jsonify({"error": "setting not found"})
        except models.lazy_record.RecordInvalid:
            return flask.jsonify({"error": "setting invalid"})

    @staticmethod
    def destroy(plant_id, id):
        try:
            setting = models.NotificationThreshold.find(id)
            setting.destroy()
            return ('', 200)
        except:
            return ("{'error': 'setting not found'}", 404)

@router.route("/api/plants/<plant_id>/logs", only=["index"])
class APILogsController(object):

    @staticmethod
    def index(plant_id):
        try:
            plant = models.Plant.for_slot(plant_id)
            data = {"id": plant.id}
            sensors = set(models.SensorDataPoint.SENSORS)
            for sensor in sensors:
                data[sensor] = [s.sensor_value for s in getattr(plant.sensor_data_points, sensor)()]
            return flask.jsonify(data)
        except models.lazy_record.RecordNotFound:
            return flask.jsonify({"error": "plant not found"})


@router.route("/api/settings", only=["index", "update"])
class APIGlobalSettingsController(object):

    @staticmethod
    def index():
        def present_time(time):
            if time is None:
                return None
            else:
                time = datetime.datetime.combine(datetime.date.today(),
                                                 time)
                return time.strftime("%X")

        controls = models.GlobalSetting.controls
        return flask.jsonify({
            control.name : {
                'enabled': control.enabled is not False,
                'id': control.id,
                'active': control.active,
                'active_start': present_time(control.active_start),
                'active_end': present_time(control.active_end),
            }
            for control in controls
        })

    @staticmethod
    def update(id):
        def get_time(time):
            if time is None:
                return None
            h, m, s = map(int, time.split(":"))
            return datetime.time(h, m, s)

        params = json.loads(flask.request.data)
        if params["active"] is True and params["enabled"] is False:
            return ('', 400)
        try:
            control = models.GlobalSetting.controls.find(id)
            enabled = params.get('enabled', False)
            active_start = params.get('active_start', None)
            active_end = params.get('active_end', None)
            control.update(enabled=enabled,
                           active_start=get_time(active_start),
                           active_end=get_time(active_end))
            control.save()
            if not params["active"] and control.active is True:
                control.temporarily_disable()
            elif params["active"] and control.active is not True:
                control.activate()
            return ('', 200)
        except models.lazy_record.RecordNotFound:
            return ('', 404)

@router.route("/api/devices", only=["create"])
class APIDevicesController(object):

    @staticmethod
    def create():
        params = flask.request.form
        device_id = "".join(params["device_id"][1:-1].split())
        models.PlantDatabase.add_device(device_id)
        return '', 200


@router.route("/api/notification_settings", only=["index", "create"])
class APINotificationSettingsController(object):

    @staticmethod
    def index():
        try:
            pd_settings = models.PlantDatabase.get_notification_settings()
            g_settings = {
                'notify_plants': models.GlobalSetting.notify_plants,
                'notify_maintenance': models.GlobalSetting.notify_maintenance,
            }
            settings = dict(pd_settings)
            settings.update(g_settings)
            return flask.jsonify(settings)
        except:
            return '', 404

    @staticmethod
    def create():
        params = json.loads(flask.request.data)
        pd_params = {
            "push": params["push"],
            "email": params["email"],
        }
        models.PlantDatabase.update_notification_settings(pd_params)
        models.GlobalSetting.notify_plants = params["notify_plants"]
        models.GlobalSetting.notify_maintenance = params["notify_maintenance"]
        return '', 200


# Error Recovery

@app.errorhandler(models.lazy_record.RecordNotFound)
def rescue_record_not_found(error):
    flask.flash("Record Not Found", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

@app.errorhandler(models.PlantDatabase.CannotConnect)
def rescue_cannot_connect(error):
    flask.flash("Cannot connect to Plant Database", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

# Requests

@app.before_request
def get_token_status():
    flask.g.token_invalid = policies.TokenRefreshPolicy()\
                                    .requires_authentication()

# SocketIO

@socketio.on("request-chart", namespace="/plants")
def send_chart_data(slot_id):
    plant = models.Plant.for_slot(slot_id, False)
    presenter = presenters.ChartDataPresenter(plant)
    socketio.emit('ideal-chart-data', {
        'chart-content': presenter.ideal_chart_data()
    }, namespace="/plants/{}".format(plant.slot_id), broadcast=False)
    socketio.emit('history-chart-data', {
        'chart-content': {
            sensor: presenter.history_chart_data_for(sensor)
            for sensor in models.SensorDataPoint.SENSORS
        }
    }, namespace="/plants/{}".format(plant.slot_id), broadcast=False)

@socketio.on("request-data", namespace="/plants")
def send_data_to_client(slot_id):
    plant = models.Plant.for_slot(slot_id, False)
    if plant is None:
        return
    presenter = presenters.PlantPresenter(plant)
    socketio.emit('new-data', {
        'light': {
            'within-tolerance': presenter.within_tolerance('light'),
            'width': presenter.bar_width('light'),
            'error-width': presenter.error_bar_width('light'),
            'class': presenter.bar_class('light'),
        },
        'water': {
            'within-tolerance': presenter.within_tolerance('water'),
            'width': presenter.bar_width('water'),
            'error-width': presenter.error_bar_width('water'),
            'class': presenter.bar_class('water'),
        },
        'humidity': {
            'within-tolerance': presenter.within_tolerance('humidity'),
            'value': presenter.formatted_value('humidity'),
        },
        'temperature': {
            'within-tolerance': presenter.within_tolerance('temperature'),
            'value': presenter.formatted_value('temperature'),
        },
    }, namespace="/plants/{}".format(plant.slot_id))

@socketio.on("update-control", namespace="/settings")
def update_control(control_id, status):
    # TODO actually update the control element
    control = models.Control.find(int(control_id))
    if status == "temporary_disable":
        control.temporarily_disable()
    else:
        control.activate()
    socketio.emit('control-updated', {
        'control_id': control_id,
        'status': status
    }, namespace="/settings")

# Background Tasks

@background.task
def load_sensor_data():
    socketio.emit('data-update', True, namespace="/plants")

# Remove this for production
@background.task
def create_sensor_data(): # pragma: no cover
    import random
    sun = [25] * config.NUMBER_OF_PLANTS
    water = [20] * config.NUMBER_OF_PLANTS
    humidity = [0.67] * config.NUMBER_OF_PLANTS
    temperature = [87.1] * config.NUMBER_OF_PLANTS
    models.WaterLevel.create(level=52)
    for i in range(config.NUMBER_OF_PLANTS):
        sun[i] += random.randint(-5, 5)
        sun[i] = min(max(sun[i], 0), 100)
        water[i] += random.randint(-5, 5)
        water[i] = min(max(water[i], 0), 100)
        temperature[i] += random.uniform(-5, 5)
        temperature[i] = min(max(temperature[i], 0), 100)
        humidity[i] = random.random()
    plants = [models.Plant.for_slot(slot_id, False)
              for slot_id in range(1, config.NUMBER_OF_PLANTS + 1)]
    for index, plant in enumerate(plants):
        if plant:
            plant.record_sensor("light", sun[index])
            plant.record_sensor("water", water[index])
            plant.record_sensor("humidity", humidity[index])
            plant.record_sensor("temperature", temperature[index])

@background.task
def notify_plant_condition(): # pragma: no cover
    if models.GlobalSetting.notify_plants:
        for nt in models.NotificationThreshold.all():
            if policies.NotificationPolicy(nt).should_notify():
                services.PlantNotifier(nt).notify()

@background.task
def notify_water_level(): # pragma: no cover
    if models.GlobalSetting.notify_maintenance:
        water_level = models.WaterLevel.last()
        if policies.WaterNotificationPolicy(water_level).should_notify():
            # Implicit: water_level exists if the policy returns true
            services.WaterLevelNotifier(water_level.level).notify()

@background.task
def refresh_token(): # pragma: no cover
    if policies.TokenRefreshPolicy().requires_refresh():
        models.Token.refresh()

@background.task
def destroy_old_tokens(): # pragma: no cover
    for token in models.Token.where("created_at < ?",
                    datetime.datetime.today() - datetime.timedelta(days=1)):
        token.destroy()

@daily.task
def updated_plants(): # pragma: no cover
    for plant in models.Plant.all():
        services.PlantUpdater(plant).update()

def run(): # pragma: no cover
    background.run()
    daily.run()
    socketio.run(app, debug=config.DEBUG, host="0.0.0.0")
