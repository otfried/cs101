from cs1robots import *

load_world("../worlds/harvest2.wld")

def turn_right(robot):
  for i in range(3):
    robot.turn_left()

def goto_start(robot):
  for i in range(5):
    robot.move()
  robot.turn_left()
  robot.move()

def stairs(robot, n):
  for i in range(n):
    robot.pick_beeper()
    robot.move()
    turn_right(robot)
    robot.move()
    robot.turn_left()

def diamond(robot, n):
  for i in range(4):
    stairs(robot, n)
    robot.turn_left()

def harvest_all(robot):
  for i in range(3):
    n = 5 - 2 * i
    diamond(robot, n)
    hubo.move()
    hubo.move()

def happy_dance(robot):
  for i in range(102):
    robot.turn_left()

hubo = Robot()
hubo.set_trace("blue")

goto_start(hubo)
harvest_all(hubo)
happy_dance(hubo)

