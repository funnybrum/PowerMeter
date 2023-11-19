from common.threading import LoopingThread

from meter.sunnyboy import SunnyBoyModbusCollector
from meter.sunnyisland import SunnyIslandModbusCollector
from meter.homemanager import HomeManagerCollector
from meter.telemetry_collector import TelemetryCollector
from meter.telemetry_sender import TelemetrySender

from lib import log


class DataProcessor(LoopingThread):
    def __init__(self, thread_manager):
        LoopingThread.__init__(self, loop_interval=0.25)
        self._thread_manager = thread_manager

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
        """
        This method contained code for calculating if there is underutilization of the PV inverter. This is now part of
        the git history. The code was modified to replace the 3 different data collecting and the energy data post
        processing scripts
        """

        own_consumption_total = round(0
                                      - data["hm.grid_supply_counter"]
                                      + data["pv_inv.supply_total"]
                                      + data["bat_inv.supply_total"]
                                      - data["bat_inv.consume_total"])

        total_load = round(0
            + data["hm.grid_consume"]
            - data["hm.grid_supply"]
            + data["pv_inv.supply"]
            - data["bat_inv.consume"]
            + data["bat_inv.supply"])  # noqa

        own_consumption = round(0
                                - data["hm.grid_supply"]
                                + data["pv_inv.supply"]
                                + data["bat_inv.supply"]
                                - data["bat_inv.consume"])

        data.update({
            'total_load': round(total_load, 1),
            'own_consumption': round(own_consumption, 1),
            'own_consumption_total': round(own_consumption_total)
        })

    def loop(self):
        data = self._aggregate_data()

        if not data:
            return

        self._enrich_data(data)
        # log(data)

        self._thread_manager.get_thread(TelemetrySender).set_data(data)
