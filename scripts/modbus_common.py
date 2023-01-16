from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


class ModbusDataCollector():
    def __init__(self, registers):
        self.client = None
        self.slave = None
        self.registers = registers
        self.errors = 0
        self.success = 0

    def reset(self):
        super().reset()
        self.errors = 0
        self.success = 0

    def connect(self, host, port, slave):
        self.slave = slave
        self.client = ModbusTcpClient(host, port)
        self.client.connect()

    def read(self):
        result = {}
        for address, type, key in self.registers:
            count = 2
            if type.startswith("64"):
                count = 4
            regs_l = self.client.read_holding_registers(address=address, count=count, slave=self.slave)
            decoder = BinaryPayloadDecoder.fromRegisters(regs_l.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            dec_method = getattr(decoder, "decode_%s" % type)
            value = dec_method()
            result[key] = value

        return result
