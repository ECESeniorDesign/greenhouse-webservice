import flask
import models
import router
import config
import eventlet
eventlet.monkey_patch()
from flask_socketio import SocketIO
import jinja2
import os
import presenters
from task_runner import BackgroundTaskRunner

template_dir = os.path.join(os.path.dirname(__file__), "templates")
loader = jinja2.FileSystemLoader(template_dir)
environment = jinja2.Environment(loader=loader)

app = flask.Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
app.secret_key = config.SECRET_KEY
router = router.Router(app)
background = BackgroundTaskRunner(refresh=10)

# Routing & Controllers

@router.route("/plants", exclude=["edit", "update"])
class PlantsController(object):
    
    @staticmethod
    def index():
        plants = [(models.Plant.for_slot(slot_id, False), slot_id)
                  for slot_id in range(1, config.NUMBER_OF_PLANTS + 1)]
        return flask.render_template("plants/index.html", plants=plants)

    @staticmethod
    def new():
        plants = models.PlantDatabase.all_plants()
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

router.root(PlantsController, "index")

# Error Recovery

@app.errorhandler(models.lazy_record.RecordNotFound)
def rescue_record_not_found(error):
    flask.flash("Record Not Found", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

@app.errorhandler(models.PlantDatabase.CannotConnect)
def rescue_cannot_connect(error):
    flask.flash("Cannot connect to Plant Database", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

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
        'acidity': {
            'within-tolerance': presenter.within_tolerance('acidity'),
            'value': presenter.formatted_value('acidity'),
        },
        'temperature': {
            'within-tolerance': presenter.within_tolerance('temperature'),
            'value': presenter.formatted_value('temperature'),
        },
    }, namespace="/plants/{}".format(plant.slot_id))

# Background Tasks

@background.task
def load_sensor_data():
    socketio.emit('data-update', True, namespace="/plants")

# Remove this for production
@background.task
def create_sensor_data(): # pragma: no cover
    import random
    if config.DEBUG:
        sun = [25] * config.NUMBER_OF_PLANTS
        water = [20] * config.NUMBER_OF_PLANTS
        pH = [8.1] * config.NUMBER_OF_PLANTS
        humidity = [0.67] * config.NUMBER_OF_PLANTS
        temperature = [87.1] * config.NUMBER_OF_PLANTS
        for i in range(config.NUMBER_OF_PLANTS):
            sun[i] += random.randint(-5, 5)
            sun[i] = min(max(sun[i], 0), 100)
            water[i] += random.randint(-5, 5)
            water[i] = min(max(water[i], 0), 100)
            temperature[i] += random.uniform(-5, 5)
            temperature[i] = min(max(water[i], 0), 100)
            humidity[i] = random.random()
            pH[i] = random.random() * 14
        plants = [models.Plant.for_slot(slot_id, False)
                  for slot_id in range(1, config.NUMBER_OF_PLANTS + 1)]
        for index, plant in enumerate(plants):
            if plant:
                plant.record_sensor("light", sun[index])
                plant.record_sensor("water", water[index])
                plant.record_sensor("humidity", humidity[index])
                plant.record_sensor("acidity", pH[index])
                plant.record_sensor("temperature", temperature[index])

def run(): # pragma: no cover
    background.run()
    socketio.run(app, debug=config.DEBUG)
