import datetime

def time(input):
    if hasattr(input, 'time'):
        return input.time()
    else:
        return input
