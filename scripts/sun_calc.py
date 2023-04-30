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
IN_FILE_NAME_N = 'data/avg_power_n.csv'
IN_YEAR = "2020"
INTERPOLATION_POINTS_AROUND = 3
DATES = []
MIN_POWER = []
MAX_POWER = []
DAILY_DROPS = [13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 23, 23, 23, 24, 24, 24, 25, 25, 25, 25, 26, 26, 26, 27, 27, 27, 28, 28, 28, 28, 29, 29, 29, 30, 30, 30, 31, 31, 32, 32, 33, 34, 34, 35, 36, 36, 37, 37, 38, 39, 39, 40, 41, 41, 42, 43, 43, 44, 44, 45, 46, 46, 47, 48, 48, 49, 50, 50, 50, 50, 50, 50, 51, 51, 51, 51, 51, 51, 52, 52, 52, 52, 52, 52, 53, 53, 53, 53, 53, 53, 54, 54, 54, 54, 54, 54, 55, 53, 52, 50, 49, 47, 46, 44, 43, 42, 40, 39, 37, 36, 34, 33, 32, 30, 29, 27, 26, 24, 23, 22, 20, 19, 17, 16, 14, 13, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]


def prepare_data():
    with open(IN_FILE_NAME, newline='') as csv_file, open(IN_FILE_NAME_N, newline='') as csv_file_n:
        reader = csv.DictReader(csv_file)
        reader_n = csv.DictReader(csv_file_n)
        for row, row_n in zip(reader, reader_n):
            assert row['time'] == row_n['time']
            DATES.append(row['time'])
            MIN_POWER.append(int(row['min_power']) + int(row_n['min_power']))
            MAX_POWER.append(int(row['max_power']) + int(row_n['max_power']))


def count_zeroes_at_start(array):
    count = 0
    while array[count] == 0 and count < len(array) - 1:
        count += 1
    return count


def calculate(month, day, hour, minute):
    """
    Parameters specify the current UTC time.
    """
    dates_index = DATES.index("2020%02d%02d:%02d10" % (month, day, hour))

    times = [60 * i + 10 for i in range(-INTERPOLATION_POINTS_AROUND, INTERPOLATION_POINTS_AROUND + 1)]
    target_y = minute

    powers = [MAX_POWER[i] for i in range(dates_index - INTERPOLATION_POINTS_AROUND, dates_index + INTERPOLATION_POINTS_AROUND + 1)]

    # drop zero points, they should not be part of the spline.
    drop_from_start = count_zeroes_at_start(powers)
    drop_from_end = count_zeroes_at_start(list(reversed(powers)))

    powers = powers[drop_from_start:-drop_from_end if drop_from_end > 0 else None]
    times = times[drop_from_start:-drop_from_end if drop_from_end > 0 else None]

    if len(powers) > 3:
        # Go with the spline
        cs = CubicSpline(times, powers)

        max_sun_power = max(0, int(cs(target_y)))
    else:
        max_sun_power = 0

    day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
    min_sun_power = DAILY_DROPS[day_of_year-1] * 0.01 * max_sun_power
    send_data("power",
              {
                  "solar.expected2.max": min(max_sun_power, 3680),
                  "solar.expected2.min": min_sun_power,
                  "solar.expected_non_clipped.max": max_sun_power,
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
    prepare_data()
    while True:
        current_minute = datetime.datetime.now().minute
        now = datetime.datetime.utcnow()
        while now.minute == current_minute:
            time.sleep(1)
            now = datetime.datetime.utcnow()

        calculate(now.month, now.day, now.hour, now.minute)
        current_minute = now.minute
