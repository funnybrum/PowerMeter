from lib import log
from lib.telemetry import query_series_last_value
from common.threading import LoopingDataCollector

DATA_COLLECTION = {
    'max_pv_output': 'solar.expected.max'
}


class DataCollector(LoopingDataCollector):
    def __init__(self):
        LoopingDataCollector.__init__(self, expected_items_count=1, loop_interval=60)

    def begin(self):
        log("Starting async telemetry collector.")

    def loop(self):
        for key, metric in DATA_COLLECTION.items():
            value = query_series_last_value('power', metric, window="2m")
            if value is not None:
                self._data[key] = value
            elif key in self.get_data():
                del self._data[key]

    def end(self):
        log("Stopping async telemetry collector.")

    def reset_data(self):
        pass
