import os
if 'APP_CONFIG' not in os.environ:
    os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/bat_inverter.yaml'

"""
Based on MODBUS-HTML_SI44M-80H-13_32009R_V10
"""

import time
import datetime

from lib import log, config
from lib.quicklock import lock
from lib.telemetry import send_data_lines

from common.tracker import Tracker
from common.modbus import ModbusDataCollector, RegisterType


TRACKERS = [
    Tracker('discharge', 'inverter.battery.supply', {"source": "sunny_island", "src": "sma"}, True, True, True, False, True),
    Tracker('charge', 'inverter.battery.consume', {"source": "sunny_island", "src": "sma"}, True, True, True, False, True),
    Tracker('discharge.total', 'inverter.battery.supply.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
    Tracker('charge.total', 'inverter.battery.consume.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
    Tracker('bat.SOC', 'inverter.battery.SOC', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
    Tracker('event.code', 'inverter.battery.status', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
]

MODBUS_DATA_COLLECTOR = ModbusDataCollector([
    (30845, RegisterType.U32, 'bat.SOC'),
    (30849, RegisterType.S32_F1, 'bat.temp'),
    (31393, RegisterType.U32, 'charge'),
    (31395, RegisterType.U32, 'discharge'),
    (31397, RegisterType.U64, 'charge.total'),
    (31401, RegisterType.U64, 'discharge.total'),
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
    log("Starting SunnyIsland data collector")
    MODBUS_DATA_COLLECTOR.connect(config["address"], 502, 3)
    while True:
        current_minute = datetime.datetime.now().minute
        while datetime.datetime.now().minute == current_minute:
            update()
            time.sleep(1)
        send()
