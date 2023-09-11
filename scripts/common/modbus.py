from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


class RegisterType(object):
    class _RegisterType(object):
        def __init__(self, count, type, fix=0, nan_value=None, nan_repr=0):
            self.count = count
            self.type = type
            self.fix = fix
            self.nan_value = nan_value
            self.nan_repr = nan_repr

        def read(self, regs_l):
            decoder = BinaryPayloadDecoder.fromRegisters(regs_l.registers, byteorder=Endian.Big, wordorder=Endian.Big)
            dec_method = getattr(decoder, "decode_%s" % self.type)
            value = dec_method()
            if abs(value) == self.nan_value:
                return self.nan_repr
            if self.fix > 0:
                value = value / (10 ** self.fix)
            return value

    S16 = _RegisterType(1, '16bit_int', nan_value=0x8000, nan_repr=0)
    S16_F2 = _RegisterType(1, '16bit_int', fix=2, nan_value=0x8000, nan_repr=0)
    S32 = _RegisterType(2, '32bit_int', nan_value=0x80000000, nan_repr=0)
    S32_F1 = _RegisterType(2, '32bit_int', fix=1, nan_value=0x80000000, nan_repr=0)
    S32_F2 = _RegisterType(2, '32bit_int', fix=2, nan_value=0x80000000, nan_repr=0)
    S32_F3 = _RegisterType(2, '32bit_int', fix=3, nan_value=0x80000000, nan_repr=0)
    U16 = _RegisterType(1, '16bit_uint', nan_value=0xFFFF, nan_repr=0)
    U32 = _RegisterType(2, '32bit_uint', nan_value=0xFFFFFFFF, nan_repr=0)
    U64 = _RegisterType(4, '64bit_uint', nan_value=0xFFFFFFFFFFFFFFFF, nan_repr=0)
    TAGLIST = _RegisterType(2, '32bit_int', nan_value=0x00FFFFFD, nan_repr=None)


class ModbusDataCollector(object):
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
        for address, reg_type, key in self.registers:
            regs_l = self.client.read_holding_registers(address=address, count=reg_type.count, slave=self.slave)
            result[key] = reg_type.read(regs_l)

        return result
