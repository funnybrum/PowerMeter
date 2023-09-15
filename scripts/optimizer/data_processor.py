from common.threading import LoopingThread

from optimizer.sunnyboy import SunnyBoyModbusCollector
from optimizer.sunnyisland import SunnyIslandModbusCollector
from optimizer.homemanager import HomeManagerCollector
from optimizer.telemetry_collector import TelemetryCollector
from optimizer.telemetry_sender import TelemetrySender


class DataProcessor(LoopingThread):
    def __init__(self, thread_manager):
        LoopingThread.__init__(self, loop_interval=0.25)
        self._thread_manager = thread_manager
        self._load_history = []
        self._load_history_size = 30
        self._dv_history = []
        self._dv_history_size = 30

    def _aggregate_data(self):
        collectors = [self._thread_manager.get_thread(c) for c in [
            HomeManagerCollector,
            SunnyBoyModbusCollector,
            SunnyIslandModbusCollector,
            TelemetryCollector
        ]]

        for collector in collectors:
            if not collector or not collector.has_data():
                return

        data = {}
        for collector in collectors:
            data.update(collector.get_data())
            collector.reset_data()

        return data

    def _enrich_data(self, data):
        load = round(data["grid_consume"] - data["grid_supply"] + data["pv_supply"] - data["charge"] + data["discharge"])

        self._load_history.append(load)
        while len(self._load_history) > self._load_history_size:
            self._load_history.pop(0)

        if len(self._load_history) > self._load_history_size * 0.9:
            load_volatility = max(self._load_history) - min(self._load_history)
        else:
            load_volatility = 999

        mppt_dv = abs(data['DCV1'] - data['DCV2'])
        self._dv_history.append(mppt_dv)
        while len(self._dv_history) > self._dv_history_size:
            self._dv_history.pop(0)

        mppt_dv_min = min(self._dv_history)

        target = round(0.95 * data['max_pv_output'] - load)
        target = round(target)
        target = min(target, 3300)
        target = max(target, 0)

        force_charging = 0
        if data['max_pv_output'] > 500 and \
                data['pv_supply'] < min(data['max_pv_output'] * 0.95, data['max_pv_output']-200) and \
                data['bat.SOC'] < 95 and \
                mppt_dv_min < 4 and \
                target - data['charge'] > 300 and \
                load_volatility < 200:
            force_charging = 1

        data.update({
            'load': load,
            'load_volatility': load_volatility,
            'target': target,
            'force_charging': force_charging
        })

    def loop(self):
        data = self._aggregate_data()

        if not data:
            return

        self._enrich_data(data)

        self._thread_manager.get_thread(TelemetrySender).set_data(data)
