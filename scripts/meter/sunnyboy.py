from lib import log
from common.modbus import ModbusDataCollector, RegisterType
from common.threading import LoopingDataCollector


class SunnyBoyModbusCollector(LoopingDataCollector):
    def __init__(self, ip_addr):
        LoopingDataCollector.__init__(self, expected_items_count=9, loop_interval=5)
        self._ip_addr = ip_addr
        self._collector = ModbusDataCollector([
            (30513, RegisterType.U64, 'pv_inv.supply_total'),
            (30775, RegisterType.S32, 'pv_inv.supply'),
            (30247, RegisterType.U32, 'pv_inv.event_code'),
            (30769, RegisterType.S32_F3, "pv_inv.mppt1.A"),
            (30771, RegisterType.S32_F2, "pv_inv.mppt1.V"),
            (30773, RegisterType.S32, "pv_inv.mppt1.W"),
            (30957, RegisterType.S32_F3, "pv_inv.mppt2.A"),
            (30959, RegisterType.S32_F2, "pv_inv.mppt2.V"),
            (30961, RegisterType.S32, "pv_inv.mppt2.W"),
        ])

    def begin(self):
        log("Starting SunnyBoy async data collector.")
        self._collector.connect(host=self._ip_addr, port=502, slave=3)

    def loop(self):
        self.update_data(self._collector.read())
