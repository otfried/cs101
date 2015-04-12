#
# Control an elevator
#

from elevator import *

init_hardware()

# --------------------------------------------------------------------

def up_to_two():
  set_motor(40)
  while not get_sensor(2):
    pass
  set_motor(0)

def up_to_three():
  set_motor(40)
  while not get_sensor(3):
    pass
  set_motor(0)

def down_to_two():
  set_motor(-40)
  while not get_sensor(2):
    pass
  set_motor(0)

def down_to_one():
  set_motor(-40)
  while not get_sensor(1):
    pass
  set_motor(0)

# --------------------------------------------------------------------

