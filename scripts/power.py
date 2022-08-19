# import os
# os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/power.yaml'

import binascii
import datetime
import struct
import socket

from lib import log
from lib.telemetry import send_data_lines
from lib.quicklock import lock

from common import Tracker


TRACKERS = [
    Tracker('pconsume', 'grid.consume.flow', {"source": "sunny_home_manager", "src": "sma"}, True, True, True, False),
    Tracker('pconsumecounter', 'grid.consume.total', {"source": "sunny_home_manager", "src": "sma"}, False, False, False, True),
    Tracker('psupply', 'grid.supply.flow', {"source": "grid", "sunny_home_manager": "sma"}, True, True, True, False),
    Tracker('psupplycounter', 'grid.supply.total', {"source": "sunny_home_manager", "src": "sma"}, False, False, False, True),
    Tracker('u1', 'voltage', {"src": "sma"}, True, True, True, False, True)
]

# unit definitions with scaling
sma_units = {
    "W":    10,
    "VA":    10,
    "VAr":    10,
    "Wh":   3600,
    "kVAh":   3600000,
    "kVArh":   3600000,
    "A":    1000,
    "V":    1000,
    "°": 1000,
    "Hz": 1000,
}

# map of all defined SMA channels
# format: <channel_number>:(emparts_name>,<unit_actual>,<unit_total>)
sma_channels={
    # totals
    1:('pconsume','W','Wh'),
    2:('psupply','W','Wh'),
    3:('qconsume','VAr','kVArh'),
    4:('qsupply','VAr','kVArh'),
    9:('sconsume','VA','kVAh'),
    10:('ssupply','VA','kVAh'),
    13:('cosphi','°'),
    14:('frequency','Hz'),
    # phase 1
    21:('p1consume','W','Wh'),
    22:('p1supply','W','Wh'),
    23:('q1consume','VAr','kVArh'),
    24:('q1supply','VAr','kVArh'),
    29:('s1consume','VA','kVAh'),
    30:('s1supply','VA','kVAh'),
    31:('i1','A'),
    32:('u1','V'),
    33:('cosphi1','°'),
    # phase 2
    41:('p2consume','W','Wh'),
    42:('p2supply','W','Wh'),
    43:('q2consume','VAr','kVArh'),
    44:('q2supply','VAr','kVArh'),
    49:('s2consume','VA','kVAh'),
    50:('s2supply','VA','kVAh'),
    51:('i2','A'),
    52:('u2','V'),
    53:('cosphi2','°'),
    # phase 3
    61:('p3consume','W','Wh'),
    62:('p3supply','W','Wh'),
    63:('q3consume','VAr','kVArh'),
    64:('q3supply','VAr','kVArh'),
    69:('s3consume','VA','kVAh'),
    70:('s3supply','VA','kVAh'),
    71:('i3','A'),
    72:('u3','V'),
    73:('cosphi3','°'),
    # common
    36864:('speedwire-version',''),
}


def decode_OBIS(obis):
    measurement = int.from_bytes(obis[0:2], byteorder="big")
    raw_type = int.from_bytes(obis[2:3], byteorder="big")
    if raw_type == 4:
        datatype = "actual"
    elif raw_type == 8:
        datatype = "counter"
    elif raw_type == 0 and measurement == 36864:
        datatype = "version"
    else:
        datatype = "unknown"
        print(
            "unknown datatype: measurement {} datatype {} raw_type {}".format(
                measurement, datatype, raw_type
            )
        )
    return (measurement, datatype)


def decode_speedwire(datagram):
    emparts = {}
    # process data only of SMA header is present
    if datagram[0:3] == b"SMA":
        # datagram length
        datalength = int.from_bytes(datagram[12:14], byteorder="big") + 16
        # print('data lenght: {}'.format(datalength))
        if datalength != 54:
            # serial number
            emID = int.from_bytes(datagram[20:24], byteorder="big")
            # print('seral: {}'.format(emID))
            emparts["serial"] = emID
            # timestamp
            timestamp = int.from_bytes(datagram[24:28], byteorder="big")
            # print('timestamp: {}'.format(timestamp))
            # decode OBIS data blocks
            # start with header
            position = 28
            while position < datalength:
                # decode header
                # print('pos: {}'.format(position))
                (measurement, datatype) = decode_OBIS(datagram[position : position + 4])
                # print('measurement {} datatype: {}'.format(measurement,datatype))
                # decode values
                # actual values
                if datatype == "actual":
                    value = int.from_bytes(
                        datagram[position + 4 : position + 8], byteorder="big"
                    )
                    position += 8
                    if measurement in sma_channels.keys():
                        emparts[sma_channels[measurement][0]] = (
                            value / sma_units[sma_channels[measurement][1]]
                        )
                        emparts[sma_channels[measurement][0] + "unit"] = sma_channels[
                            measurement
                        ][1]
                # counter values
                elif datatype == "counter":
                    value = int.from_bytes(
                        datagram[position + 4 : position + 12], byteorder="big"
                    )
                    position += 12
                    if measurement in sma_channels.keys():
                        emparts[sma_channels[measurement][0] + "counter"] = (
                            value / sma_units[sma_channels[measurement][2]]
                        )
                        emparts[
                            sma_channels[measurement][0] + "counterunit"
                        ] = sma_channels[measurement][2]
                elif datatype == "version":
                    value = datagram[position + 4 : position + 8]
                    if measurement in sma_channels.keys():
                        bversion = binascii.b2a_hex(value).decode("utf-8")
                        version = (
                            str(int(bversion[0:2], 16))
                            + "."
                            + str(int(bversion[2:4], 16))
                            + "."
                            + str(int(bversion[4:6], 16))
                        )
                        revision = str(chr(int(bversion[6:8])))
                        # revision definitions
                        if revision == "1":
                            # S – Spezial Version
                            version = version + ".S"
                        elif revision == "2":
                            # A – Alpha (noch kein Feature Complete, Version für Verifizierung und Validierung)
                            version = version + ".A"
                        elif revision == "3":
                            # B – Beta (Feature Complete, Version für Verifizierung und Validierung)
                            version = version + ".B"
                        elif revision == "4":
                            # R – Release Candidate / Release (Version für Verifizierung, Validierung und Feldtest / öffentliche Version)
                            version = version + ".R"
                        elif revision == "5":
                            # E – Experimental Version (dient zur lokalen Verifizierung)
                            version = version + ".E"
                        elif revision == "6":
                            # N – Keine Revision
                            version = version + ".N"
                        # adding versionnumber to compare versions
                        version = (
                            version
                            + "|"
                            + str(bversion[0:2])
                            + str(bversion[2:4])
                            + str(bversion[4:6])
                        )
                        emparts[sma_channels[measurement][0]] = version
                    position += 8
                else:
                    position += 8
    return emparts


def get_socket():
    ipbind = '0.0.0.0'
    MCAST_GRP = '239.12.255.254'
    MCAST_PORT = 9522

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    try:
        mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(ipbind))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except BaseException as e:
        print('could not connect to mulicast group or bind to given interface')
        raise e

    return sock


def update(sock):
    data_dict = decode_speedwire(sock.recv(608))

    if len(data_dict) == 0:
        return

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
    sock = get_socket()
    while True:
        current_minute = datetime.datetime.now().second
        while datetime.datetime.now().second == current_minute:
            update(sock)
        send()
