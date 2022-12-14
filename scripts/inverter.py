# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/inverter1.yaml'

import time
import datetime
import requests

from urllib3.exceptions import InsecureRequestWarning

from lib import log, config
from lib.quicklock import lock
from lib.telemetry import send_data_lines

from common import Tracker

TRACKERS = [
    Tracker('yield', 'inverter.supply.flow', {"source": "sunny_boy", "src": "sma"}, True, True, True, False, True),
    Tracker('yield_counter', 'inverter.supply.total', {"source": "sunny_boy", "src": "sma"}, False, False, False, True, False)
]


def extract(props, key, default=0):
    return props[key]["1"][0]["val"] if props[key]["1"][0]["val"] else 0


def update():
    if datetime.datetime.now().second % 5 != 0:
        return

    response_data = requests.get("https://%s/dyn/getDashValues.json" % config["address"], verify=False).json()

    data_root = list(response_data["result"].keys())[0]
    props = response_data["result"][data_root]
    data_dict = {
        "yield": extract(props, "6100_40263F00"),
        "yield_counter": extract(props, "6400_00260100")
    }

    for tracker in TRACKERS:
        tracker.track(data_dict)


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
    log("Starting SunnyBoy data collector")
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    while True:
        current_minute = datetime.datetime.now().minute
        while datetime.datetime.now().minute == current_minute:
            update()
            time.sleep(1)
        send()
