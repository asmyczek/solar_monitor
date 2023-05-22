# Generic tools and functions for all controllers
from network import WLAN, AP_IF, STA_IF
from machine import reset, Timer
import time, uasyncio, ntptime
import config

#
# Network
# Use setup_network() on boot and watch_network() in app loop
#

WIFI_IF = WLAN(STA_IF)
RETRY = 0

# Connect to AP
def _connect_to_ap():
    WIFI_IF.active(True)
    WIFI_IF.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    RETRY = 0
    while (not WIFI_IF.isconnected()) and RETRY < 10:
        time.sleep_ms(100)
        RETRY += 1
        if RETRY > 10:
            print('Unable to connect to WIFI for 2 seconds, will retry in 1 minute.')
    if WIFI_IF.isconnected():
        try:
            ntptime.settime()
        except OSError as e:
            print(e)
        print('Network configuration: {}'.format(WIFI_IF.ifconfig()))

# Setup network on boot
def setup_network():
    WLAN(AP_IF).active(False)
    _connect_to_ap()

# Network watch, initialize in application loop
async def watch_network():
    while True:
        if not WIFI_IF.isconnected():
            _connect_to_ap()
        await uasyncio.sleep(60)


#
# Watch dog
#

class WatchDog:

    def __init__(self, timeout=60):
        self.timeout = timeout
        self.timer = Timer(1)
        self.init()

    def init(self):
        self.counter = 0
        self.timer.init(period=1000, callback=self.count, mode=Timer.PERIODIC)

    def count(self, t):
        self.counter += 1
        if self.counter >= self.timeout:
            print('WDT - rebooting...')
            reset()

    def feed(self):
        self.counter = 0

    def deinit(self):
        self.timer.deinit()

WDT = WatchDog()

# Comment for dev
WDT.deinit()
