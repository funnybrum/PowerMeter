# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/power.yaml'

import datetime

from lib import log
from lib.telemetry import send_data_lines
from lib.quicklock import lock

from common.tracker import Tracker
from common.speedwire import get_speedwire_socket, decode_speedwire

TRACKERS = [
    Tracker('pconsume', 'grid.consume.flow', {"src": "sma"}, True, True, True, False),
    Tracker('pconsumecounter', 'grid.consume.total', {"src": "sma"}, False, False, False, True),
    Tracker('psupply', 'grid.supply.flow', {"src": "sma"}, True, True, True, False),
    Tracker('psupplycounter', 'grid.supply.total', {"src": "sma"}, False, False, False, True),
    Tracker('u1', 'voltage', {"src": "sma"}, True, True, True, False, True)
]


def update(sw_socket):
    data_dict = decode_speedwire(sw_socket.recv(608))

    if data_dict.get("serial", None) != 3012881242:
        return

    if len(data_dict) == 0:
        return

    for tracker in TRACKERS:
        try:
            tracker.track(data_dict)
        except Exception as e:
            print(repr(e), data_dict)


def send():
    data_lines = []
    for tracker in TRACKERS:
        data_lines.extend(tracker.get_data_lines())
        tracker.reset()

    send_data_lines("power", data_lines)
    # for data_line in data_lines:
    #     print(data_line)


if __name__ == "__main__":
    try:
        lock()
    except RuntimeError:
        exit(0)
    log("Starting SMA HomeManager 2.0 data collector")
    sock = get_speedwire_socket()
    while True:
        current_minute = datetime.datetime.now().minute
        while datetime.datetime.now().minute == current_minute:
            update(sock)
        send()
