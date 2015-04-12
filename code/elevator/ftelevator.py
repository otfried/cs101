#
# Hardware interface for Fischertechnik elevator
#
# Channel assignment:
# 11: Floor 1 lamp
# 10: Floor 2 lamp down
#  9: Floor 2 lamp up
#  8: Floor 3 lamp
#  7: Floor 3 button
#  6: Floor 1 button
#  5: NC
#  4: Floor 2 button up 
#  3: Sensor floor 1
#  2: Floor 2 button down 
#  1: Sensor floor 3 (reflectance sensor)
#  0: Sensor floor 2
#

import time as _time

# map button number to channel
button_map = [6, 2, 4, 7]
# map sensor number to channel
sensor_map = [3, 0, 1]

immediate_door = False

channel = None
motor_channel = None

# --------------------------------------------------------------------

def motor_send(a):
  motor_channel.write(a)
  motor_channel.flush()

def send(a, recv = None):
  channel.write(a)
  channel.flush()
  if recv:
    s = channel.read(recv)
    return s

def down_to_first():
  if get_sensor(1):
    return
  set_motor(-127)
  while not get_sensor(1):
    pass
  set_motor(0)

# --------------------------------------------------------------------

def init_hardware():
  global channel, channel_in, motor_channel
  channel = open("/dev/ttyACM0", "w+b")
  motor_channel = open("/dev/ttyACM1", "wb")
  motor_send("\xaa")
  for i in range(4):
    set_light(i, False)
  send("\x84\x05\x00\x00")
  down_to_first()

# --------------------------------------------------------------------

def set_motor(arg):
  """Set motor speed: > 0 up, < 0 down, 0 stop."""
  if arg > 127 or arg < -127:
    raise ValueError("Illegal motor speed")
  if arg >= 0:
    motor_send("\x88" + chr(arg))
  else:
    motor_send("\x8a" + chr(-arg))

def set_light(num, state):
  """Set light on or off.  Lights are numbered 0 .. 3."""
  if num < 0 or num > 3:
    raise ValueError("Illegal light number""")
  ch = chr(11 - num)
  if state:
    s = "\x00\x7f"
  else:
    s = "\x00\x00"
  send("\x84" + ch + s)

def get_button(num):
  """Test if button is pressed. Buttons are numbered 0 .. 3."""
  if num < 0 or num > 3:
    raise ValueError("Illegal button number""")
  ch = chr(button_map[num])
  resp = send("\x90" + ch, 2)
  val = ord(resp[0]) + ord(resp[1]) * 256
  return val < 500

def get_sensor(floor):
  """Test if floor sensor activated.  Floors are 1 .. 3.""" 
  if floor < 1 or floor > 3:
    raise ValueError("Illegal floor number""")
  ch = chr(sensor_map[floor-1])
  resp = send("\x90" + ch, 2)
  val = ord(resp[0]) + ord(resp[1]) * 256
  return val < 100

# --------------------------------------------------------------------

def open_door():
  """Open elevator door"""
  if not immediate_door:
    for i in range(2):
      send("\x84\x05\x00\x7f")
      _time.sleep(0.1)
      send("\x84\x05\x00\x00")
      _time.sleep(0.1)
  send("\x84\x05\x00\x7f")

def close_door():
  """Close elevator door"""
  if not immediate_door:
    for i in range(2):
      send("\x84\x05\x00\x00")
      _time.sleep(0.1)
      send("\x84\x05\x00\x7f")
      _time.sleep(0.1)
  send("\x84\x05\x00\x00")

# --------------------------------------------------------------------
