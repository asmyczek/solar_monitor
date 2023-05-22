from micropython import alloc_emergency_exception_buf
from uio import StringIO
import uasyncio, time, ujson, sys
from machine import RTC, Pin, I2C
from besp import WDT, watch_network
import config
from umqtt.robust import MQTTClient as BaseMQTTClient
import ssd1306


# Uncomment for debugging
alloc_emergency_exception_buf(100)

LOOP = None

METRICS = {
    config.MQTT_TOPIC_MAIN_LINE_STATUS      : 0,
    config.MQTT_TOPIC_BATTERY_CHARGE_LEVEL  : 0,
    config.MQTT_TOPIC_SOLAR_PRODUCTION      : 0,
    config.MQTT_TOPIC_CONSUMPTION_L1        : 0,
    config.MQTT_TOPIC_CONSUMPTION_L2        : 0,
    config.MQTT_TOPIC_CONSUMPTION_L3        : 0
}

VALID_TOPICS = set(METRICS.keys())

### Display ###


class Display(object):

    def __init__(self):
        self._display = self._create_display()

    def _create_display(self):
        i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
        return ssd1306.SSD1306_I2C(128, 64, i2c)

    def _print_source(self, on_grid):
        self._display.fill(0)

        if on_grid:
            self._display.text('Grid', 46, 28, 1)
            self._display.hline(20, 14, 88, 1)
            self._display.vline(20, 14, 36, 1)
            self._display.hline(20, 50, 88, 1)
            self._display.vline(108, 14, 36, 1)
            self._display.contrast(0)
            self._display.show()
        else:
            pass

        self._display.show()

    def _print_battery_status(self, percentage):
        pass

    def _print_consumption(self, percentage):
        pass

    def update_display(self, metric, value):
        if METRICS[metric] != value:
            METRICS[metric] = value

            on_grid = METRICS[config.MQTT_TOPIC_MAIN_LINE_STATUS] == 1
            consumption = (METRICS[config.MQTT_TOPIC_SOLAR_PRODUCTION]
                           - METRICS[config.MQTT_TOPIC_CONSUMPTION_L1]
                           - METRICS[config.MQTT_TOPIC_CONSUMPTION_L2]
                           - METRICS[config.MQTT_TOPIC_CONSUMPTION_L3])

            if metric == config.MQTT_TOPIC_MAIN_LINE_STATUS:
                self._print_source(on_grid)

            if not on_grid:
                if metric == config.MQTT_TOPIC_BATTERY_CHARGE_LEVEL:
                    self._print_battery_status(METRICS[config.MQTT_TOPIC_BATTERY_CHARGE_LEVEL])
                else:
                    self._print_consumption(consumption)

            print('{} - {},{}'.format(on_grid, 
                                      consumption,
                                      METRICS[config.MQTT_TOPIC_BATTERY_CHARGE_LEVEL]))
        
        WDT.feed()


### MQTT ###

class MQTTClient(object):

    def __init__(self):
        self._display = Display()
        self._client = self._create_client()

    def _create_client(self):
        client = BaseMQTTClient(config.MQTT_CLIENT_NAME,
                            config.MQTT_HOST,
                            user=config.MQTT_USER,
                            password=config.MQTT_PASSWORD,
                            port=config.MQTT_PORT)
        client.set_callback(self.on_message)
        if not client.connect(clean_session=False):
            print("MQTT new session being set up.")
        for k in VALID_TOPICS: 
            client.subscribe(k, qos=2)
        return client

    def check_msg(self):
        if self._client:
            self._client.check_msg()
            self._client.publish(topic='stats/{}/up/status', msg='up')

    def on_message(self, btopic, bmessage):
        topic = btopic.decode("utf-8")
        if topic in VALID_TOPICS and bmessage:
            val = ujson.loads(bmessage)["value"]
            self._display.update_display(topic, int(val) if val else 0.0)
        else:
            print('Invalid topic {}! Value {}'.format(topic, bmessage))



### Main ###

def exception_handler(loop, context):
    trace = StringIO()
    sys.print_exception(context["exception"], trace)  
    trace = trace.getvalue().split('\n')
    for s in trace:
        print(s)
    with open ('error.log', 'a') as f:
        for l in trace:
            f.write('{}\n'.format(l)) 


async def start_monitor():
    mqtt_client = MQTTClient()
    time.sleep_ms(500)

    try:
        while True:
            mqtt_client.check_msg()
            await uasyncio.sleep(1)
    except Exception as e:
        print(e)
    finally:
        # TODO: add last will
        mqtt_client.disconnect()
        print('Monitor stopped.')
        LOOP.stop()

def main():
    print('Starting monitor: {}'.format(RTC().datetime()))

    global LOOP

    LOOP = uasyncio.get_event_loop()
    LOOP.set_exception_handler(exception_handler)
    LOOP.create_task(start_monitor())
    LOOP.create_task(watch_network())

    print('Monitor started')
    try:
        LOOP.run_forever()
    except Exception as e:
        print(e)
    finally:
        print('Monitor stopped.')
        LOOP.stop()
