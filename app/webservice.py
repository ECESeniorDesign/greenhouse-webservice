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
                  for slot_id in (1, 2)]
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
                                     plant=plant)

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
        'chart-content': presenter.history_chart_data()
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
        sun = [25, 25]
        water = [20, 15]
        pH = [8.1, 6.2]
        humidity = [0.67, 0.71]
        for i in range(2):
            sun[i] += random.randint(-5, 5)
            sun[i] = min(max(sun[i], 0), 100)
            water[i] += random.randint(-5, 5)
            water[i] = min(max(water[i], 0), 100)
            humidity[i] = random.random()
            pH[i] = random.random() * 14
        plants = [models.Plant.for_slot(1, False),
                  models.Plant.for_slot(2, False)]
        for index, plant in enumerate(plants):
            if plant:
                plant.record_sensor("light", sun[index])
                plant.record_sensor("water", water[index])
                plant.record_sensor("humidity", humidity[index])
                plant.record_sensor("acidity", pH[index])

def run(): # pragma: no cover
    background.run()
    socketio.run(app, debug=config.DEBUG)
