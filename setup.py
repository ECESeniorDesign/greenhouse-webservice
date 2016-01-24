import sys
from app.config import DATABASE, SCHEMA
import lazy_record

def main():
    if sys.argv[1] == "db":
        lazy_record.connect_db(DATABASE)
        with open(SCHEMA) as schema:
            lazy_record.load_schema(schema.read())

if __name__ == '__main__':
    main()