from cs1robots import *
#create_world()
load_world("../worlds/harvest2.wld")

hubo = Robot(orientation = "N")
hubo.set_trace("blue")
hubo.set_pause(0.1)

def move_and_pick():
  if hubo.on_beeper():
    hubo.pick_beeper()
  hubo.move()

def turn_right():
  for i in range(3):
    hubo.turn_left()

def move_9():
  for i in range(11):
    move_and_pick()

def zigzag():
  move_9()
  turn_right()
  hubo.move()
  turn_right()
  move_9()

def zig():
  zigzag()
  hubo.turn_left()
  hubo.move()
  hubo.turn_left()

zig()
zig()
zig()
zig()
zig()

