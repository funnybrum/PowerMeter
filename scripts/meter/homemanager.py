from common.threading import LoopingDataCollector

from lib import log
from common.speedwire import get_speedwire_socket, decode_speedwire


class HomeManagerCollector(LoopingDataCollector):

    COLLECTION_KEYS_MAP = {
        "pconsume": "hm.grid_consume",
        "psupply": "hm.grid_supply",
        "u1": "hm.grid_voltage",
        "pconsumecounter": "hm.grid_consume_counter",
        "psupplycounter": "hm.grid_supply_counter",
        "cosphi": "hm.grid_factor"
    }

    def __init__(self):
        LoopingDataCollector.__init__(self, expected_items_count=6, loop_interval=0.1)
        self._sw_socket = None

    def begin(self):
        log("Starting HomeManager async data collector.")
        self._sw_socket = get_speedwire_socket()

    def loop(self):
        data_dict = decode_speedwire(self._sw_socket.recv(608))

        if data_dict.get("serial", None) != 3012881242:
            return

        if len(data_dict) == 0:
            return

        new_data = {}
        for key, key_t in self.COLLECTION_KEYS_MAP.items():
            if key in data_dict:
                new_data[key_t] = data_dict[key]
        self.update_data(new_data)

    def end(self):
        log("Stopping HomeManager async data collector.")
