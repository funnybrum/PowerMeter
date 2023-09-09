# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/pv_inverter.yaml'

"""
Based on MODBUS-HTML_SB30-50-1AV-40_V10
"""

import time
import datetime

from lib import log, config
from lib.quicklock import lock
from lib.telemetry import send_data_lines

from common.tracker import Tracker
from common.modbus import ModbusDataCollector, RegisterType


TRACKERS = [
    Tracker('yield', 'inverter.supply.flow', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('yield.total', 'inverter.supply.total', {"source": "sunny_boy", "src": "sma"}, False, False, False, True, False),
    Tracker('DCV1', 'inverter.dc.voltage.mppt1', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('DCA1', 'inverter.dc.current.mppt1', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('DCW1', 'inverter.dc.power.mppt1', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('DCV2', 'inverter.dc.voltage.mppt2', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('DCA2', 'inverter.dc.current.mppt2', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('DCW2', 'inverter.dc.power.mppt2', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('event.code', 'inverter.pv.status', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
]

MODBUS_DATA_COLLECTOR = ModbusDataCollector([
    (30513, RegisterType.U64, 'yield.total'),
    (30769, RegisterType.S32_F3, "DCA1"),
    (30771, RegisterType.S32_F2, "DCV1"),
    (30773, RegisterType.S32, "DCW1"),
    (30775, RegisterType.S32, 'yield'),
    (30957, RegisterType.S32_F3, "DCA2"),
    (30959, RegisterType.S32_F2, "DCV2"),
    (30961, RegisterType.S32, "DCW2"),
    (30247, RegisterType.U32, 'event.code'),
])


def update():
    if datetime.datetime.now().second % 5 != 0:
        return

    data_dict = MODBUS_DATA_COLLECTOR.read()
    for tracker in TRACKERS:
        tracker.track(data_dict)


def send():
    data_lines = []
    for tracker in TRACKERS:
        data_lines.extend(tracker.get_data_lines())
        tracker.reset()

    send_data_lines("power", data_lines)
    # print("=" * 40)
    # for data_line in data_lines:
    #     print(data_line)


if __name__ == "__main__":
    try:
        lock()
    except RuntimeError:
        exit(0)
    log("Starting SunnyBoy data collector")
    MODBUS_DATA_COLLECTOR.connect(config["address"], 502, 3)
    while True:
        current_minute = datetime.datetime.now().minute
        while datetime.datetime.now().minute == current_minute:
            update()
            time.sleep(1)
        send()
