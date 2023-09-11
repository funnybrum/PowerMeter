from lib import log
from common.modbus import ModbusDataCollector, RegisterType
from common.threading import LoopingDataCollector


class SunnyIslandModbusCollector(LoopingDataCollector):
    def __init__(self, ip_addr):
        LoopingDataCollector.__init__(self, expected_items_count=3, loop_interval=1)
        self._ip_addr = ip_addr
        self._collector = ModbusDataCollector([
            (30845, RegisterType.U32, 'bat.SOC'),
            (31393, RegisterType.U32, 'charge'),
            (31395, RegisterType.U32, 'discharge'),
        ])

    def begin(self):
        log("Starting SunnyIsland async data collector.")
        self._collector.connect(host=self._ip_addr, port=502, slave=3)

    def loop(self):
        self.update_data(self._collector.read())

    def end(self):
        log("Stopping SunnyIsland async data collector.")
