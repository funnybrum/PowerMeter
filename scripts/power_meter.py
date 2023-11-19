import os

if 'APP_CONFIG' not in os.environ:
    os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/power_meter.yaml'

"""
Electricity data collector, processor and telemetry generator.

Collects data from the SMA Home Manager 2.0, the Sunny Boy inverter, the Sunny Island inverter. The data is enriched and
send to an InfluxDB.
"""

from signal import signal, SIGINT, SIGTERM

from lib import config, log
from lib.quicklock import lock

from common.threading import ThreadManager
from meter.sunnyboy import SunnyBoyModbusCollector
from meter.sunnyisland import SunnyIslandModbusCollector
from meter.homemanager import HomeManagerCollector
from meter.telemetry_collector import TelemetryCollector
from meter.telemetry_sender import TelemetrySender
from meter.data_processor import DataProcessor

manager = ThreadManager(loop_interval=1)


def checker(thread_manager):
    if not manager.get_thread(HomeManagerCollector):
        manager.add_and_run(HomeManagerCollector())

    if not manager.get_thread(SunnyIslandModbusCollector):
        manager.add_and_run(SunnyIslandModbusCollector(ip_addr=config["bat_inv_addr"]))

    if not manager.get_thread(SunnyBoyModbusCollector):
        manager.add_and_run(SunnyBoyModbusCollector(ip_addr=config["pv_inv_addr"]))

    if not manager.get_thread(TelemetryCollector):
        manager.add_and_run(TelemetryCollector())

    if not manager.get_thread(TelemetrySender):
        manager.add_and_run(TelemetrySender())

    if not manager.get_thread(DataProcessor):
        manager.add_and_run(DataProcessor(manager))


def handle_kill_signal(sig, frame):
    manager.stop()


if __name__ == "__main__":
    try:
        lock()
    except RuntimeError:
        exit(0)
    log("Starting Power Meter 2.0")

    signal(SIGINT, handle_kill_signal)
    signal(SIGTERM, handle_kill_signal)

    manager.set_thread_checker(checker)
    manager.run()

