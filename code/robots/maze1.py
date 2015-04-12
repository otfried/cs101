# This program lets the robot go around his world counterclockwise,
# stopping when he comes back to his starting point.

from cs1robots import *

load_world("../worlds/maze1.wld")

hubo = Robot(beepers = 10)
hubo.set_trace("blue")

def turn_right():
  for i in range(3): 
    hubo.turn_left()

def mark_starting_point_and_move():
  hubo.drop_beeper()
  while not hubo.front_is_clear():
    hubo.turn_left()
  hubo.move()

def follow_right_wall():
  if hubo.right_is_clear():
    # Keep to the right
    turn_right()
    hubo.move()
  elif hubo.front_is_clear(): 
    # move following the right wall
    hubo.move()
  else:
    # follow the wall
    hubo.turn_left()

# end of definitions, begin solution

mark_starting_point_and_move()
            
finished = hubo.on_beeper
print type(finished)
while not finished():
  follow_right_wall()
