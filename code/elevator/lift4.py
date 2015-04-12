#
# Control an elevator
#

from dualator import *
import time

init_hardware()

# all requests currently waiting to be served
pending = [ False, False, False, False ]

# possible states
(WAIT1, WAIT2, WAIT3, MOVE12, MOVE21, MOVE23, MOVE32, 
 OPEN1, OPEN2UP, OPEN2DOWN, OPEN3) = range(11)

# current state
state = WAIT1

# countdown for open door and length of open door period
open_count = 0
OPEN_LENGTH = 20

# --------------------------------------------------------------------

def check_buttons(skip = []):
  """Check all buttons and set lights and requests, but skip 
  buttons in list skip."""
  for i in range(4):
    if not (i in skip) and get_button(i):
      pending[i] = True
      set_light(i, True)

def request_done(num):
  """Mark request num as done and turn off light."""
  pending[num] = False
  set_light(num, False)

# --------------------------------------------------------------------

def start_move(new_state):
  """Turn on motor, and set state to new_state."""
  global state
  if new_state == MOVE12 or new_state == MOVE23:
    set_motor(+80)
  else:
    set_motor(-80)
  state = new_state
    
def start_wait(new_state):
  """Stop motor and start waiting for a request using new_state."""
  global state
  set_motor(0)
  state = new_state

def set_open_counter():
  global open_count
  open_count = OPEN_LENGTH

def start_open(new_state):
  """Stop motor, open the door, start open period, 
  and set state to new_state."""
  global state
  set_motor(0)
  open_door()
  set_open_counter()
  state = new_state

def open_ended():
  """Check if open period ended. If so, close door and return True."""
  global open_count
  if open_count > 0:
    open_count -= 1
    time.sleep(0.1) # wait a bit, but not to long to miss buttons
    return False
  else:
    close_door()
    return True

# --------------------------------------------------------------------

def wait1():
  check_buttons([0])
  if get_button(0):
    start_open(OPEN1)
  elif pending[1] or pending[2] or pending[3]:
    start_move(MOVE12)

def wait2():
  check_buttons([1, 2])
  if get_button(1):
    start_open(OPEN2DOWN)
  elif get_button(2):
    start_open(OPEN2UP)
  elif pending[0]:
    start_move(MOVE21)
  elif pending[3]:
    start_move(MOVE23)

def wait3():
  check_buttons([3])
  if get_button(3):
    start_open(OPEN3)
  elif pending[0] or pending[1] or pending[2]:
    start_move(MOVE32)

# --------------------------------------------------------------------

def move12():
  global state
  check_buttons()
  if not get_sensor(2):
    return
  # reached 2nd floor - should we stop here?
  if pending[2]:
    request_done(2)
    start_open(OPEN2UP)
  elif pending[3]:
    # continue going up
    state = MOVE23
    return
  elif pending[0] or pending[1]:
    # someone wants to go down
    request_done(1)
    start_open(OPEN2DOWN)
  else: # arrived, but no more request
    start_wait(WAIT2)

def move21():
  check_buttons()
  if not get_sensor(1):
    return
  # arrived at 1st floor
  if pending[0] or pending[1] or pending[2] or pending[3]:
    request_done(0)
    start_open(OPEN1)
  else: # no request
    start_wait(WAIT1)
    
def move23():
  check_buttons()
  if not get_sensor(3):
    return
  # arrived at 3rd floor
  if pending[0] or pending[1] or pending[2] or pending[3]:
    request_done(3)
    start_open(OPEN3)
  else: # no request
    start_wait(WAIT3)
    
def move32():
  global state
  check_buttons()
  if not get_sensor(2):
    return
  # reached 2nd floor - should we stop here?
  if pending[1]:
    request_done(1)
    start_open(OPEN2DOWN)
  elif pending[0]:
    # continue going down
    state = MOVE21
    return
  elif pending[3] or pending[2]:
    # someone wants to go up
    request_done(2)
    start_open(OPEN2UP)
  else: # arrived, but no more request
    start_wait(WAIT2)

# --------------------------------------------------------------------

def open1():
  check_buttons([0])
  if get_button(0):
    set_open_counter()
  if open_ended():
    if pending[1] or pending[2] or pending[3]:
      start_move(MOVE12)
    else:
      start_wait(WAIT1)

def open2up():
  check_buttons([2])
  if get_button(2):
    set_open_counter()
  if open_ended():
    if pending[3]:
      start_move(MOVE23)
    elif pending[1]:
      request_done(1)
      start_open(OPEN2DOWN)
    elif pending[0]:
      start_move(MOVE21)
    else:
      start_wait(WAIT2)

def open2down():
  check_buttons([2])
  if get_button(2):
    set_open_counter()
  if open_ended():
    if pending[0]:
      start_move(MOVE21)
    elif pending[2]:
      request_done(2)
      start_open(OPEN2UP)
    elif pending[3]:
      start_move(MOVE23)
    else:
      start_wait(WAIT2)

def open3():
  check_buttons([3])
  if get_button(3):
    set_open_counter()
  if open_ended():
    if pending[0] or pending[1] or pending[2]:
      start_move(MOVE32)
    else:
      start_wait(WAIT3)

# --------------------------------------------------------------------

handler = [ wait1, wait2, wait3, move12, move21, move23, move32,
            open1, open2up, open2down, open3 ]

state = WAIT1
while True:
  handler[state]()
  
# --------------------------------------------------------------------
