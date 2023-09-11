from abc import abstractmethod
from threading import Thread
from time import time, sleep

from lib import log


class LoopingThread(Thread):
    def __init__(self, loop_interval=1):
        Thread.__init__(self)
        self._running = True
        self._loop_interval = loop_interval

    def run(self):
        try:
            self.begin()
            start = time()
            while self._running:
                self.loop()
                while self._running and time() < start + self._loop_interval:
                    sleep(0.1)
                start += self._loop_interval
        finally:
            self.end()

    def begin(self):
        pass

    def end(self):
        pass

    @abstractmethod
    def loop(self):
        pass

    def stop(self):
        self._running = False


class LoopingDataCollector(LoopingThread):
    def __init__(self, expected_items_count, loop_interval=1):
        LoopingThread.__init__(self, loop_interval=loop_interval)
        self._data = {}
        self._expected_items_count = expected_items_count

    def loop(self):
        self._data.update(self._collector.read())

    def has_data(self):
        return len(self._data) >= self._expected_items_count

    def get_data(self):
        return self._data

    def update_data(self, new_data):
        self._data.update(new_data)

    def reset_data(self):
        self._data.clear()


class ThreadManager(LoopingThread):
    def __init__(self, loop_interval=5):
        LoopingThread.__init__(self, loop_interval)
        self._threads = [self]
        self._check_threads_are_alive_callback = None

    def begin(self):
        log("Starting")

    def end(self):
        log("Stopping")

    def loop(self):
        # In some cases we may run the thread manager instead of starting it. Check if th == self too.
        self._threads = [th for th in self._threads if th.is_alive() or th == self]
        self._check_threads_are_alive_callback(self)

    def set_thread_checker(self, thread_checker):
        self._check_threads_are_alive_callback = thread_checker

    def add_and_run(self, thread):
        thread.start()
        self._threads.append(thread)

    def get_thread(self, clazz):
        for thread in self._threads:
            if isinstance(thread, clazz):
                return thread

    def stop(self):
        for th in self._threads[1:]:
            th.stop()

        self._running = False
