from lib import log
from common.modbus import ModbusDataCollector, RegisterType
from common.threading import LoopingDataCollector


class SunnyBoyModbusCollector(LoopingDataCollector):
    def __init__(self, ip_addr):
        LoopingDataCollector.__init__(self, expected_items_count=3, loop_interval=1)
        self._ip_addr = ip_addr
        self._collector = ModbusDataCollector([
            (30771, RegisterType.S32_F2, "DCV1"),
            (30959, RegisterType.S32_F2, "DCV2"),
            (30775, RegisterType.S32, 'pv_supply'),
        ])

    def begin(self):
        log("Starting SunnyBoy async data collector.")
        self._collector.connect(host=self._ip_addr, port=502, slave=3)

    def loop(self):
        self.update_data(self._collector.read())
