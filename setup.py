import sys
import app.config as config
import lazy_record
import app.models as models
import app.webservice
import app.seeds
from app.lib.coffee import coffee

def main():
    if sys.argv[1] == "db":
        lazy_record.connect_db(config.DATABASE)
        with open(config.SCHEMA) as schema:
            lazy_record.load_schema(schema.read())
        app.seeds.seed()
    elif sys.argv[1] in ("server", "s"):
        # Remove these for production
        import mock
        app.webservice.models.services.ControlCluster.bus = mock.Mock(
            name="bus")
        coffee(app.webservice.app)
        app.webservice.models.lazy_record.connect_db(config.DATABASE)
        app.webservice.run()
    elif sys.argv[1] == "console":
        app.webservice.models.lazy_record.connect_db(config.DATABASE)

if __name__ == '__main__':
    main()
