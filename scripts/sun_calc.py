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
INTERPOLATION_POINTS_AROUND = 3
DATES = []
MAX_POWER = []


def prepare_data():
    with open(IN_FILE_NAME, newline='') as csv_file, open(IN_FILE_NAME_N, newline='') as csv_file_n:
        reader = csv.DictReader(csv_file)
        reader_n = csv.DictReader(csv_file_n)
        for row, row_n in zip(reader, reader_n):
            assert row['time'] == row_n['time']
            DATES.append(row['time'])
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

    send_data("power",
              {
                  "solar.expected.max": min(max_sun_power, 3680),
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
