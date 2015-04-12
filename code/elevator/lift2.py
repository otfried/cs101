#
# Control an elevator
#

from elevator import *

init_hardware()

# --------------------------------------------------------------------

def move_to_floor(speed, floor):
  set_motor(speed)
  while not get_sensor(floor):
    pass
  set_motor(0)

def wait_for_button():
  """Wait for a button and return number."""
  while True:
    for i in range(4):
      if get_button(i):
        return i

current_floor = 1

def goto_floor(floor):
  global current_floor
  if floor == current_floor:
    return
  speed = 80
  if floor < current_floor:
    speed = -80
  move_to_floor(speed, floor)
  current_floor = floor

while True:
  request = wait_for_button()
  set_light(request, True)
  floor = (request + 1) // 2 + 1
  goto_floor(floor)
  set_light(request, False)

# --------------------------------------------------------------------
