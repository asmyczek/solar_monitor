import gc, webrepl, esp, time
from besp import setup_network

esp.osdebug(None)
gc.collect()

setup_network()
time.sleep_ms(500)

#webrepl.start()
