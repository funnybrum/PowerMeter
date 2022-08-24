# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/sun_calc.yaml'

import csv
import datetime
import time

from scipy.interpolate import CubicSpline

from lib import log
from lib.telemetry import send_data
from lib.quicklock import lock

IN_FILE_NAME = 'data/avg_power.csv'
IN_YEAR = "2020"
INTERPOLATION_POINTS_AROUND = 3
DATES = []
MIN_POWER = []
MAX_POWER = []

with open(IN_FILE_NAME, newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        DATES.append(row['time'])
        MIN_POWER.append(row['min_power'])
        MAX_POWER.append(row['max_power'])


def calculate(month, day, hour, minute):
    """
    Parameters specify the current UTC time.
    """
    dates_index = DATES.index("2020%02d%02d:%02d10" % (month, day, hour))

    times = [60 * i + 10 for i in range(-INTERPOLATION_POINTS_AROUND, INTERPOLATION_POINTS_AROUND + 1)]
    target_y = minute

    powers = [MAX_POWER[i] for i in range(dates_index - INTERPOLATION_POINTS_AROUND, dates_index + INTERPOLATION_POINTS_AROUND + 1)]
    cs = CubicSpline(times, powers)
    max_sun_power = max(0, int(cs(target_y)))

    powers = [MIN_POWER[i] for i in range(dates_index - INTERPOLATION_POINTS_AROUND, dates_index + INTERPOLATION_POINTS_AROUND + 1)]
    cs = CubicSpline(times, powers)
    min_sun_power = max(0, int(cs(target_y)))

    send_data("power",
              {
                  "solar.expected.max": max_sun_power,
                  "solar.expected.min": min_sun_power
              },
              {
                  "src": "master_mind"
              })


if __name__ == "__main__":
    try:
        lock()
    except RuntimeError:
        exit(0)
    log("Starting available power data calculator")
    while True:
        current_minute = datetime.datetime.now().minute
        now = datetime.datetime.utcnow()
        while now.minute == current_minute:
            time.sleep(1)
            now = datetime.datetime.utcnow()

        calculate(now.month, now.day, now.hour, now.minute)
        current_minute = now.minute
