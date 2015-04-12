#
# Control an elevator
#

from elevator import *

init_hardware()

# all requests currently waiting to be served
pending = [ False, False, False, False ]

current_floor = 1

# --------------------------------------------------------------------

def check_buttons():
  """Check all buttons and set lights and requests."""
  for i in range(4):
    if get_button(i):
      pending[i] = True
      set_light(i, True)

def get_request():
  """Return one pending request, wait if none pending."""
  while True:
    for i in range(4):
      if pending[i]:
        return i
    # no pending request, check buttons again
    check_buttons()

def move_to_floor(speed, floor):
  set_motor(speed)
  while not get_sensor(floor):
    check_buttons()
  set_motor(0)

def goto_floor(floor):
  global current_floor
  if floor == current_floor:
    return
  speed = 80
  if floor < current_floor:
    speed = -80
  move_to_floor(speed, floor)
  current_floor = floor
  # request served
  if floor == 1:
    pending[0] = False
    set_light(0, False)
  elif floor == 2:
    for i in range(1,3):
      pending[i] = False
      set_light(i, False)
  else:
    pending[3] = False
    set_light(3, False)

# --------------------------------------------------------------------

while True:
  request = get_request()
  floor = (request + 1) // 2 + 1
  goto_floor(floor)

# --------------------------------------------------------------------
