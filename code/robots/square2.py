from cs1robots import *
create_world()
hubo = Robot(orientation = "N")
hubo.set_trace("blue")

def turn_right():
  hubo.turn_left()
  hubo.turn_left()
  hubo.turn_left()

def move_9():
  hubo.move()
  hubo.move()
  hubo.move()
  hubo.move()
  hubo.move()
  hubo.move()
  hubo.move()
  hubo.move()
  hubo.move()

move_9()
turn_right()
move_9()
turn_right()
move_9()
turn_right()
move_9()
