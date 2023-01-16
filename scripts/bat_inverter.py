# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/bat_inverter.yaml'

import time
import datetime

from lib import log, config
from lib.quicklock import lock
from lib.telemetry import send_data_lines

from common import Tracker
from modbus_common import ModbusDataCollector


TRACKERS = [
    Tracker('discharge', 'inverter.battery.supply', {"source": "sunny_island", "src": "sma"}, True, True, True, False, True),
    Tracker('charge', 'inverter.battery.consume', {"source": "sunny_island", "src": "sma"}, True, True, True, False, True),
    Tracker('discharge.total', 'inverter.battery.supply.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
    Tracker('charge.total', 'inverter.battery.consume.total', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
    Tracker('SOC', 'inverter.battery.SOC', {"source": "sunny_island", "src": "sma"}, False, False, False, True, False),
]

MODBUS_DATA_COLLECTOR = ModbusDataCollector([
    (30845, '32bit_uint', 'SOC'),
    (31393, '32bit_uint', 'charge'),
    (31395, '32bit_uint', 'discharge'),
    (31397, '64bit_uint', 'charge.total'),
    (31401, '64bit_uint', 'discharge.total'),
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
