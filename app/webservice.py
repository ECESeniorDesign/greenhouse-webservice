import flask
import models
import router
import config

app = flask.Flask(__name__)
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
        try:
            plant.save()
            flask.flash("'{}' successfully added.".format(plant.name))
            return flask.redirect(flask.url_for('PlantsController.show',
                                                id=plant.slot_id))
        except models.lazy_record.RecordInvalid:
            flask.flash("Could not add plant.")
            return flask.redirect(flask.url_for('PlantsController.index'))

    @staticmethod
    def show(id):
        plant = models.Plant.for_slot(id)
        return flask.render_template("plants/show.html",
                                     plant=plant)

    @staticmethod
    def destroy(id):
        plant = models.Plant.for_slot(id)
        plant.destroy()
        return flask.redirect(flask.url_for('PlantsController.index'))

@app.errorhandler(models.lazy_record.RecordNotFound)
def redirect_to_index(error):
    flask.flash("Record Not Found", 'error')
    return flask.redirect(flask.url_for('PlantsController.index'))

router.root(PlantsController, "index")
