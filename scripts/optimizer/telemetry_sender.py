from common.threading import LoopingThread
from lib import log
from lib.telemetry import to_data_line, send_data_lines


MAPPING = {
    "grid_supply": "grid.supply.flow",
    "grid_consume": "grid.consume.flow",
    "pv_supply": "inverter.supply.flow",
    "charge": "inverter.battery.consume",
    "discharge": "inverter.battery.supply",
    "target": "inverter.consume.target",
    "load": "system.load",
    "load_volatility": "system.load.volatility",
    "force_charging": "force_charging"
}


class TelemetrySender(LoopingThread):
    def __init__(self, db="ptest"):
        LoopingThread.__init__(self, loop_interval=10)
        self._db = db
        self._data = {}

    def begin(self):
        log("Starting telemetry sender")

    def loop(self):
        lines = []
        processed_keys = []
        for key, value in self._data.items():
            if key == "load_volatility":
                if value > 200:
                    self._loop_interval = 0.2
                else:
                    self._loop_interval = 10
            if key in MAPPING:
                lines.append(to_data_line(MAPPING[key], value, {}))
            processed_keys.append(key)

        for key in processed_keys:
            del self._data[key]

        if len(lines) > 0:
            send_data_lines(self._db, lines)

    def end(self):
        log("Stopping telemetry sender")

    def set_data(self, data):
        self._data.update(data)
