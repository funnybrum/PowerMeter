from common.threading import LoopingDataCollector

from lib import log
from common.speedwire import get_speedwire_socket, decode_speedwire


class HomeManagerCollector(LoopingDataCollector):
    def __init__(self):
        LoopingDataCollector.__init__(self, expected_items_count=2, loop_interval=1)
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
        for key, key_t in [("pconsume", "grid_consume"), ("psupply", "grid_supply")]:
            if key in data_dict:
                new_data[key_t] = data_dict[key]
        self.update_data(new_data)

    def end(self):
        log("Stopping HomeManager async data collector.")

