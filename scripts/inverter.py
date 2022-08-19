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


def update():
    if datetime.datetime.now().second % 5 != 0:
        return

    response_data = requests.get("https://%s/dyn/getDashValues.json" % config["address"], verify=False).json()

    data_root = list(response_data["result"].keys())[0]
    props = response_data["result"][data_root]
    data_dict = {
        "yield": props["6100_40263F00"]["1"][0]["val"],
        "yield_counter": props["6400_00260100"]["1"][0]["val"]
    }

    for tracker in TRACKERS:
        tracker.track(data_dict)


def send():
    data_lines = []
    log("Collected %d data points. Sending telemetry." % TRACKERS[0].get_points_count())
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
