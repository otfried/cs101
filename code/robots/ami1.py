from cs1robots import *

create_world()
hubo = Robot("light_blue")
hubo.turn_left()
hubo.move()
hubo.turn_left()
hubo.turn_left()
hubo.turn_left()

ami = Robot("purple")
ami.move()
hubo.move()

for i in range(8):
  hubo.move()
  ami.move()
