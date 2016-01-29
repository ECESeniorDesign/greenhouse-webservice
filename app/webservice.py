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

template_dir = os.path.join(os.path.dirname(__file__), "templates")
loader = jinja2.FileSystemLoader(template_dir)
environment = jinja2.Environment(loader=loader)

app = flask.Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
app.secret_key = config.SECRET_KEY
router = router.Router(app)


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

@app.errorhandler(models.lazy_record.RecordNotFound)
def rescue_record_not_found(error):
    flask.flash("Record Not Found", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

@app.errorhandler(models.PlantDatabase.CannotConnect)
def rescue_cannot_connect(error):
    flask.flash("Cannot connect to Plant Database", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

router.root(PlantsController, "index")
