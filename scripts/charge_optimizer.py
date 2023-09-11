import os

if 'APP_CONFIG' not in os.environ:
    os.environ['APP_CONFIG'] = '/brum/dev/PowerMeter/scripts/config/charge_optimizer.yaml'

"""
This script optimizes the PV system by reducing the required time to increase the Sunny Island battery charge power. To
accomplish this all system components are being monitored (PV inverter output and MPPT tracker status, Sunny Island
inverter status and Home Manager 2.0 stats for grid load. Once there is unutilized PV power (the Sunny Boy is throttled)
the Sunny Island is being forced to increase the power consumption. This results in reduced battery charging power ramp
up rates.

The Grid Tie SMA PV system that is AC coupled is introducing serious delay in the battery inverter charging ramp up
rate. After a sudden drop in the energy consumption by appliances the SMA Home Manager cuts both the Sunny Boy power
output and the Sunny Island load (for charging the battery). It takes over 20 minutes in some cases to fully load the
PV inverter. When there is often energy load on the system the impact is that the utilized PV power can drop severely.
"""

from signal import signal, SIGINT, SIGTERM

from lib import config, log
from lib.quicklock import lock

from common.threading import ThreadManager
from optimizer.sunnyboy import SunnyBoyModbusCollector
from optimizer.sunnyisland import SunnyIslandModbusCollector
from optimizer.homemanager import HomeManagerCollector
from optimizer.telemetry_collector import TelemetryCollector
from optimizer.telemetry_sender import TelemetrySender
from optimizer.data_processor import DataProcessor

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
    log("Starting charge optimizer")

    signal(SIGINT, handle_kill_signal)
    signal(SIGTERM, handle_kill_signal)

    manager.set_thread_checker(checker)
    manager.run()

