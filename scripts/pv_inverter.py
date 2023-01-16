# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/pv_inverter.yaml'

import time
import datetime

from lib import log, config
from lib.quicklock import lock
from lib.telemetry import send_data_lines

from common import Tracker
from modbus_common import ModbusDataCollector


TRACKERS = [
    Tracker('yield', 'inverter.supply.flow', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('yield.total', 'inverter.supply.total', {"source": "sunny_boy", "src": "sma"}, False, False, False, True, False)
]

MODBUS_DATA_COLLECTOR = ModbusDataCollector([
    (30775, '32bit_uint', 'yield'),
    (30513, '64bit_uint', 'yield.total'),
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
