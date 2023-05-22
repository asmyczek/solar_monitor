from monitor.main import LOOP
from besp import WDT
import machine
import os


print('Stopping watchdog process...')
WDT.deinit()

print("""
Commands:
  reboot    - reboot monitor
  ls        - list current dir
  stop      - stop application loop
  cat_error - cat error file
  rm_error  - remove error file
""")

# Reboot ESP
def reboot():
    machine.reset()

# List current dir, avoids another import
def ls():
    print(os.listdir())

# Stop app loop
def stop():
    if LOOP:
        LOOP.stop()

# Print error from file
def cat_error():
    try:
        f = open('error.log', 'r')
        print(f.read())
        f.close()
    except OSError:
        print('No error file.')

# Remove error file
def rm_error():
    try:
        os.remove('error.log')
        print('Error file removed.')
    except OSError:
        print('No error file.')
