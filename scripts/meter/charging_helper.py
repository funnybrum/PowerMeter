import os
if 'APP_CONFIG' not in os.environ:
    os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/power_meter.yaml'


"""
Frozen for now. This may be resurrected in the future for improving the system recovery after grid supply spike.
"""


from threading import Thread

from time import sleep

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client import ModbusTcpClient


class ChargeRampUpHelper(Thread):
    _instance = None
    _can_instantiate = False
    _iteration_count = 30

    def __init__(self):
        if not self._can_instantiate:
            raise RuntimeError("Use .get_instance()")
        Thread.__init__(self)
        self._run = True
        self._charging_target = None
        self._remaining_iterations = ChargeRampUpHelper._iteration_count

    @staticmethod
    def get_instance():
        if ChargeRampUpHelper._instance is None or not ChargeRampUpHelper._instance.is_alive():
            ChargeRampUpHelper._can_instantiate = True
            ChargeRampUpHelper._instance = ChargeRampUpHelper()
            ChargeRampUpHelper._can_instantiate = False
        return ChargeRampUpHelper._instance

    def _set_addr(self, address, value, type, client):
        if not self._charging_target:
            print("No target specified")
            return

        if self._charging_target <= 0:
            print("Invalid target specified")
            return

        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        if (type == "uint32"):
            builder.add_32bit_uint(value)
        elif (type == "int32"):
            builder.add_32bit_int(value)
        else:
            raise ValueError()

        registers = builder.to_registers()
        # print("set_addr(%s, %s)" % (address, value))
        client.write_registers(address, registers, slave=3)

    def run(self):
        with ModbusTcpClient("192.168.1.212", port=502, unit_id=3, auto_open=True, auto_close=True) as client:
            self._set_addr(40151, 802, "uint32", client)
            while self._remaining_iterations > 0:
                self._remaining_iterations -= 1
                self._set_addr(40149, -self._charging_target, "int32", client)
                sleep(1)
            self._set_addr(40151, 803, "uint32", client)

    def stop(self):
        self._run = False

    def set_charging_power_target(self, target):
        self._charging_target = target
