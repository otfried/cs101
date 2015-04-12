from cs1robots import *
create_world(avenues = 5, streets = 5)

hubo = Robot(beepers = 10)
hubo.set_trace("blue")

def dance():
  for i in range(4):
    hubo.turn_left()

def move_or_turn():
  if hubo.front_is_clear():
    dance()
    hubo.move()
  else:
    hubo.turn_left()
    hubo.drop_beeper()

for i in range(18):
  move_or_turn()
