import sys
import app.config as config
import lazy_record
import app.models as models
import app.webservice

def main():
    if sys.argv[1] == "db":
        lazy_record.connect_db(config.DATABASE)
        with open(config.SCHEMA) as schema:
            lazy_record.load_schema(schema.read())
    elif sys.argv[1] in ("server", "s"):
        app.webservice.models.lazy_record.connect_db(config.DATABASE)
        app.webservice.app.run()
    elif sys.argv[1] == "console":
        app.webservice.models.lazy_record.connect_db(config.DATABASE)

if __name__ == '__main__':
    main()