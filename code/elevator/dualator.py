
import elevator
import ftelevator

# --------------------------------------------------------------------

def init_hardware():
  ftelevator.immediate_door = True
  ftelevator.init_hardware()
  elevator.init_hardware()

def set_motor(arg):
  ftelevator.set_motor(arg)

def set_light(num, state):
  ftelevator.set_light(num, state)
  elevator.set_light(num, state)

def get_button(num):
  return ftelevator.get_button(num)

def get_sensor(floor):
  s = ftelevator.get_sensor(floor)
  if s:
    elevator._cabin.moveTo(70, 800 - 90 - 200 * floor)
  return s

def open_door():
  ftelevator.open_door()
  elevator.open_door()
  
def close_door():
  elevator.close_door()
  ftelevator.close_door()
  
# --------------------------------------------------------------------
