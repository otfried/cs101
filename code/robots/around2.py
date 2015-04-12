from cs1robots import *
create_world(avenues = 5, streets = 5)

hubo = Robot(beepers = 10)
hubo.set_trace("blue")

def turn_right():
  for i in range(3): 
    hubo.turn_left()

hubo.drop_beeper()
hubo.move()
while not hubo.on_beeper():
  if hubo.right_is_clear():
    turn_right()
  elif hubo.front_is_clear():
    hubo.move()
  else:
    hubo.turn_left()
