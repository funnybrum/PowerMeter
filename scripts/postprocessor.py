# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/postprocessor.yaml'

"""
Based on MODBUS-HTML_SB30-50-1AV-40_V10
"""

from datetime import datetime
from dateutil.parser import parse
from time import sleep

from lib import log, config
from lib.quicklock import lock
from lib.telemetry import send_data_lines, query_data, to_data_line



OWN_CONSUMPTION_KEY = "pv.consume.flow.avg"


def backfill(from_date, window="30m"):
    """
    Backfill the data for from_date - window to from_date.

    Fresh data (younger than 10 minutes) is filled conditionally - only if both PV and battery inverter data is
    available. Older than 10 minutes data is filled unconditionally - missing data is filled with zeroes.

    Note: does not duplicate existing pv.consume.flow.avg points.
    """
    def query_series(to_ts, metric, default="null"):
        result = query_data(
            "power",
            'SELECT LAST("value") '
            'FROM "%s" '
            'WHERE time >= %ds - %s AND time < %ds '
            'GROUP BY time(1m) fill(%s)' % (metric, to_ts, window, to_ts, default))
        if not result:
            return {}
        return {
            entry['time']: entry['last'] for entry in result[0][1]
        }

    # Round the from_ts to be at the minute start. Without this some data points emitted at round minute will be lost.
    to_ts = round(from_date.timestamp())
    to_ts = to_ts - (to_ts % 60)
    pv_supply = query_series(to_ts, "inverter.supply.flow.avg")
    bat_consume = query_series(to_ts, "inverter.battery.consume.avg")
    bat_supply = query_series(to_ts, "inverter.battery.supply.avg")
    own_consume = query_series(to_ts, OWN_CONSUMPTION_KEY)

    keyset = set()
    keyset.update(pv_supply.keys())
    keyset.update(bat_consume.keys())
    keyset.update(bat_supply.keys())
    ts_now = round(datetime.now().timestamp())

    data_points = []
    for key in sorted(keyset):
        if key in own_consume and own_consume.get(key) is not None:
            # Existing value, no need to backfill it.
            continue
        ts = round(parse(key).timestamp())
        pv_s = pv_supply.get(key, 0)
        bat_s = bat_supply.get(key, 0)
        bat_c = bat_consume.get(key, 0)
        if pv_s is None or bat_s is None or bat_c is None:
            # Missing data detected. If older than 10 minutes - backfill. Else - skip.
            if ts_now - ts < 600:
                continue
        if pv_s is None:
            pv_s = 0
        if bat_s is None:
            bat_s = 0
        if bat_c is None:
            bat_c = 0
        own_c = round(pv_s + bat_s - bat_c, 1)
        data_points.append(to_data_line(OWN_CONSUMPTION_KEY, own_c, {"src": "master_mind"}, ts))

    send_data_lines("power", data_points)


if __name__ == "__main__":
    try:
        lock()
    except RuntimeError:
        exit(0)
    log("Starting data post-processor")
    current_minute = datetime.now().minute
    while True:
        if datetime.now().second > 10:
            current_minute = datetime.now().minute
        while datetime.now().minute == current_minute:
            sleep(1)
        backfill(datetime.now())
        sleep(20)  # should be more than the if condition seconds (datetime.now().second > 10)