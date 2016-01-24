import flask
import models
import router

app = flask.Flask(__name__)
router = router.Router(app)


@router.route("/plants", only=["index", "new"])
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

router.root(PlantsController, "index")

if __name__ == '__main__':
    app.run()
