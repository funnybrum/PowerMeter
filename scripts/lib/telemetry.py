import dateutil.parser
import math

from datetime import datetime
from influxdb import InfluxDBClient


def _get_influx_client(db):
    host = '192.168.1.200'
    port = 8086
    return InfluxDBClient(host=host, port=port, database=db)


def query_data(database, query):
    client = _get_influx_client(database)
    result = client.query(query)
    return result.items()


def send_data_lines(database, data_lines):
    """
    :param database: the database to publish to
    :param data_lines: array of data lines in the InfluxDB line format protocol
    """
    client = _get_influx_client(database)
    client.write(data_lines, {'db': database, 'precision': 's'}, protocol='line')


def to_data_line(metric, value, tags, timestamp=None):
    def escape(val):
        if not isinstance(val, str):
            return val
        return val.replace(' ', '\\ ').replace(',', '\\,')

    tags_string = ",".join(["%s=%s" % (t_key, escape(t_value)) for t_key, t_value in tags.items()])
    if len(tags_string) > 0:
        tags_string = ',' + tags_string
    point_line = "%s%s value=%s" % (metric, tags_string, value)
    if timestamp:
        point_line += " %s" % int(timestamp)

    return point_line


def send_data(database, data, tags={}, timestamp=None):
    """
    :param database: the database to publish to
    :param data: dict with key representing the metric name and value representing the data point value
    :param tags: dict with tags to be added to the data point
    :param timestamp: timestamp in seconds to be applied to the metric
    """

    data_points = []
    for metric, value in data.items():
        data_points.append(to_data_line(metric, value, tags, timestamp))

    send_data_lines(database, data_points)


def date_to_timestamp(timedate_str):
    _time = dateutil.parser.parse(timedate_str)
    return int((_time.replace(tzinfo=None) - datetime(1970, 1, 1)).total_seconds())


def rh_to_ah(temp, rh):
    # https://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/
    p_sat = 6.112 * math.exp((17.67 * temp) / (temp + 243.5))
    abs_humidity = (p_sat * rh * 2.167428434) / (273.15 + temp)
    return round(abs_humidity, 2)


def pressure_converter(sea_pressure, temp, altitude):
    # https://keisan.casio.com/exec/system/1224575267
    p = sea_pressure / math.pow(1 - 0.0065 * altitude / (temp + 0.0065 * altitude + 273.15), -5.257)
    return round(p)


def query_series_last_value(db, metric, window="10m", default=None):
    result = query_data(
        db,
        'SELECT LAST("value") '
        'FROM "%s" '
        'WHERE time >= now() - %s ' % (metric, window))
    if not result:
        return None
    return next(result[0][1])['last']
