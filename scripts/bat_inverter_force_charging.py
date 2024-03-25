import time

from datetime import datetime

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client import ModbusTcpClient

client = None


def getClient():
    global client
    if client is None:
        client = ModbusTcpClient("192.168.1.212", port=502, unit_id=3, auto_open=True, auto_close=True)
        client.connect()
    return client


def setAddr(address, value, type):
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
    if (type == "uint32"):
        builder.add_32bit_uint(value)
    elif (type == "int32"):
        builder.add_32bit_int(value)
    else:
        raise ValueError()
    registers = builder.to_registers()
    getClient().write_registers(address, registers, slave=3)


if __name__ == "__main__":
    now = datetime.now()
    getClient()

    setAddr(40151, 802, "uint32")
    while now.hour < 6 or now.hour >= 22:
        now = datetime.now()
        print("Executing %s" % datetime.now())
        setAddr(40149, -1500, "int32")
        time.sleep(3)

    setAddr(40151, 803, "uint32")
