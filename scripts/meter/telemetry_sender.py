from common.threading import LoopingThread
from lib import log
from lib.telemetry import to_data_line, send_data_lines
from common.tracker import Tracker
from datetime import datetime


MAPPING = {
    "grid_supply": "grid.supply.flow",
    "grid_consume": "grid.consume.flow",
    "pv_supply": "inverter.supply.flow",
    "charge": "inverter.battery.consume",
    "discharge": "inverter.battery.supply",
    "target": "inverter.consume.target",
    "load": "system.load",
    "load_volatility": "system.load.volatility",
    "base_load": "system.load.base",
    "force_charging": "force_charging",
    "load_avg": "system.load.avg",
    "DCV1": "mppt1.voltage",
    "DCV2": "mppt2.voltage"
}

TRACKERS = [
    # Grid data trackers
    Tracker('hm.grid_consume', 'grid.consume.flow', {"src": "sma"}, True, True, True, False, True),
    Tracker('hm.grid_consume_counter', 'grid.consume.total', {"src": "sma"}, False, False, False),
    Tracker('hm.grid_supply', 'grid.supply.flow', {"src": "sma"}, True, True, True, False),
    Tracker('hm.grid_supply_counter', 'grid.supply.total', {"src": "sma"}, False, False, False, True),
    Tracker('hm.grid_voltage', 'voltage', {"src": "sma"}, True, True, True, False),
    Tracker('hm.grid_factor', 'grid.factor', {"src": "sma"}, True, True, True, False),
    # PV inverter data trackers
    Tracker('pv_inv.supply', 'inverter.supply.flow', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('pv_inv.supply_total', 'inverter.supply.total', {"source": "sunny_boy", "src": "sma"}, False, False, False, True),
    Tracker('pv_inv.mppt1.V', 'inverter.dc.voltage.mppt1', {"source": "sunny_boy", "src": "sma"}, True, True, True, False),
    Tracker('pv_inv.mppt1.A', 'inverter.dc.current.mppt1', {"source": "sunny_boy", "src": "sma"}, True, True, True, False),
    Tracker('pv_inv.mppt1.W', 'inverter.dc.power.mppt1', {"source": "sunny_boy", "src": "sma"}, True, True, True, False),
    Tracker('pv_inv.mppt2.V', 'inverter.dc.voltage.mppt2', {"source": "sunny_boy", "src": "sma"}, True, True, True, False),
    Tracker('pv_inv.mppt2.A', 'inverter.dc.current.mppt2', {"source": "sunny_boy", "src": "sma"}, True, True, True, False),
    Tracker('pv_inv.mppt2.W', 'inverter.dc.power.mppt2', {"source": "sunny_boy", "src": "sma"}, True, True, True, False),
    Tracker('pv_inv.event_code', 'inverter.pv.status', {"source": "sunny_island", "src": "sma"}, False, False, False, True),
    # Battery inverter data trackers
    Tracker('bat_inv.supply', 'inverter.battery.supply', {"source": "sunny_island", "src": "sma"}, True, True, True, False, True),
    Tracker('bat_inv.consume', 'inverter.battery.consume', {"source": "sunny_island", "src": "sma"}, True, True, True, False),
    Tracker('bat_inv.supply_total', 'inverter.battery.supply.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True),
    Tracker('bat_inv.consume_total', 'inverter.battery.consume.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True),
    Tracker('bat_inv.SOC', 'inverter.battery.SOC', {"source": "sunny_island", "src": "sma"}, False, False, False, True),
    Tracker('bat_inv.event_code', 'inverter.battery.status', {"source": "sunny_island", "src": "sma"}, False, False, False, True),
    # Calculated data trackers
    Tracker('own_consumption', 'pv.consume.flow', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('own_consumption_total', 'pv.consume.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True),
    Tracker('total_load', 'energy.consume.flow', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
]

class TelemetrySender(LoopingThread):
    def __init__(self, db="power"):
        LoopingThread.__init__(self, loop_interval=5, align_to_round_minute=True)
        self._db = db
        self._data = {}
        self._last_data_minute_ts = datetime.now().minute

    def begin(self):
        log("Starting telemetry sender")

    def loop(self):
        if datetime.now().minute != self._last_data_minute_ts:
            self._last_data_minute_ts = datetime.now().minute
            lines = []
            point_date = datetime.now().replace(second=0, microsecond=0)
            point_date = round(point_date.timestamp())
            for tracker in TRACKERS:
                lines.extend(tracker.get_data_lines(timestamp=point_date))
                tracker.reset()
                send_data_lines(self._db, lines)

        if self._data:
            for tracker in TRACKERS:
                tracker.track(self._data)

        self._data.clear()

    def end(self):
        log("Stopping telemetry sender")

    def set_data(self, data):
        self._data.update(data)
