from lib import log
from common.modbus import ModbusDataCollector, RegisterType
from common.threading import LoopingDataCollector


class SunnyIslandModbusCollector(LoopingDataCollector):
    def __init__(self, ip_addr):
        LoopingDataCollector.__init__(self, expected_items_count=6, loop_interval=1)
        self._ip_addr = ip_addr
        self._collector = ModbusDataCollector([
            (30845, RegisterType.U32, 'bat_inv.SOC'),
            (31393, RegisterType.U32, 'bat_inv.consume'),
            (31395, RegisterType.U32, 'bat_inv.supply'),
            (31397, RegisterType.U64, 'bat_inv.consume_total'),
            (31401, RegisterType.U64, 'bat_inv.supply_total'),
            (30247, RegisterType.U32, 'bat_inv.event_code'),
            (30915, RegisterType.U32, 'bat_inv.power_status'),
        ])

    def begin(self):
        log("Starting SunnyIsland async data collector.")
        self._collector.connect(host=self._ip_addr, port=502, slave=3)

    def loop(self):
        self.update_data(self._collector.read())

    def end(self):
        log("Stopping SunnyIsland async data collector.")
