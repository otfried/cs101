import math
from cs1graphics import *

def animate_sunrise(sun):
  w = canvas.getWidth()
  h = canvas.getHeight()
  r = sun.getRadius()
  x0 = w / 2.0
  y0 = h + r
  xradius = w / 2.0 - r
  yradius = h
  for angle in range(181):
    rad = (angle/180.0) * math.pi
    x = x0 - xradius * math.cos(rad)
    y = y0 - yradius * math.sin(rad)
    sun.moveTo(x, y)

canvas = Canvas(600, 200)
canvas.setBackgroundColor("dark blue")

sun = Circle(30)
sun.setFillColor("yellow")
canvas.add(sun)

animate_sunrise(sun)
