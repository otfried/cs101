from cs1robots import *
create_world()
hubo = Robot()
hubo.set_trace("blue")

def step_back():
  hubo.turn_left()
  hubo.turn_left()
  hubo.move()
  hubo.turn_left()
  hubo.turn_left()

hubo.move()
step_back()
