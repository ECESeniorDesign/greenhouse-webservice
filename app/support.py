import datetime

def time(input):
    if isinstance(input, datetime.datetime):
        return input.time()
    elif isinstance(input, datetime.time):
        return input
