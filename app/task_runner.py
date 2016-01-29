import time
from threading import Thread

class BackgroundTaskRunner(object):

    def __init__(self, refresh=10):
        self.refresh = refresh
        self.tasks = []

    @property
    def task(self):
        def wrapper(task):
            self.tasks.append(task)
            return task
        return wrapper

    def run(self): # pragma: no cover

        def worker():
            while True:
                for task in self.tasks:
                    task()
                time.sleep(self.refresh)

        worker_thread = Thread(target=worker)
        worker_thread.daemon = True
        worker_thread.start()
        return worker_thread
