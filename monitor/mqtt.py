from umqtt.robust import MQTTClient
import uasyncio, time, machine, ujson
import config


def float_from_json(value):
    return float(ujson.loads(value)["value"])

TOPICS = {
    config.MQTT_TOPIC_MAIN_LINE_STATUS      : float_from_json,
    config.MQTT_TOPIC_BATTERY_CHARGE_LEVEL  : float_from_json,
    config.MQTT_TOPIC_SOLAR_PRODUCTION      : float_from_json,
    config.MQTT_TOPIC_CONSUMPTION_L1        : float_from_json,
    config.MQTT_TOPIC_CONSUMPTION_L2        : float_from_json,
    config.MQTT_TOPIC_CONSUMPTION_L3        : float_from_json
}

VALID_TOPICS = set(TOPICS.keys())

class Client(object):

    def __init__(self):
        self._monitor_callback = None
        self._client = self._create_client()

    def _create_client(self):
        client = MQTTClient(config.MQTT_CLIENT_NAME,
                            config.MQTT_HOST,
                            user=config.MQTT_USER,
                            password=config.MQTT_PASSWORD,
                            port=config.MQTT_PORT)
        client.set_callback(self.on_message)
        if not client.connect(clean_session=False):
            print("MQTT new session being set up.")
        for k in list(TOPICS.keys()): 
            client.subscribe(k, qos=2)
        return client

    def set_monitor_callback(self, callback):
        self._monitor_callback = callback

    def check_msg(self):
        if self._client:
            self._client.check_msg()
            self._client.publish(topic='stats/{}/up/status', msg='up')

    def on_message(self, btopic, bmessage):
        topic = btopic.decode("utf-8")
        if topic in VALID_TOPICS and bmessage and self._monitor_callback:
            #.decode("utf-8")
            self._monitor_callback(topic, TOPICS[topic](bmessage))
        else:
            print('Invalid topic {}! Value {}'.format(topic, bmessage))


CLIENT = Client()


async def start_mqtt_client():
    while True:
        CLIENT.check_msg()
        await uasyncio.sleep(1)

    # TODO: add last will
    CLIENT.disconnect()