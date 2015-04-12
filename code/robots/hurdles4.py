
from cs1robots import *
load_world("../worlds/hurdles3.wld")

hubo = Robot()
hubo.set_trace("blue")

def turn_right():
  for i in range(3):
    hubo.turn_left()

def jump_one_hurdle():
  hubo.turn_left()
  hubo.move()
  turn_right()
  hubo.move()
  turn_right()
  hubo.move()
  hubo.turn_left()

def move_jump_or_finish():
  # test for end of race
  if hubo.on_beeper(): 
    pass  # race is over - do nothing
  # is there a hurdle?
  elif hubo.front_is_clear(): 
    hubo.move()
  else:
    jump_one_hurdle()

for i in range(20):
  move_jump_or_finish()
