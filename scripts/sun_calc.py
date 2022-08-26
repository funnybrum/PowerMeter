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
DAILY_DROPS = [13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 23, 23, 23, 24, 24, 24, 25, 25, 25, 25, 26, 26, 26, 27, 27, 27, 28, 28, 28, 28, 29, 29, 29, 30, 30, 30, 31, 31, 32, 32, 33, 34, 34, 35, 36, 36, 37, 37, 38, 39, 39, 40, 41, 41, 42, 43, 43, 44, 44, 45, 46, 46, 47, 48, 48, 49, 50, 50, 50, 50, 50, 50, 51, 51, 51, 51, 51, 51, 52, 52, 52, 52, 52, 52, 53, 53, 53, 53, 53, 53, 54, 54, 54, 54, 54, 54, 55, 53, 52, 50, 49, 47, 46, 44, 43, 42, 40, 39, 37, 36, 34, 33, 32, 30, 29, 27, 26, 24, 23, 22, 20, 19, 17, 16, 14, 13, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]

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

    # powers = [MIN_POWER[i] for i in range(dates_index - INTERPOLATION_POINTS_AROUND, dates_index + INTERPOLATION_POINTS_AROUND + 1)]
    # cs = CubicSpline(times, powers)
    # min_sun_power = max(0, int(cs(target_y)))

    day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
    min_sun_power = DAILY_DROPS[day_of_year-1] * 0.01 * max_sun_power

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
