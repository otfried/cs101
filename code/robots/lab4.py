import math

sin = math.sin
pi = math.pi

for i in range(41):
  x = float(i) / 40.0 * 2 * pi
  y = sin(x)
  p = int((y + 1.0)/2.0 * 78)
  print "#" * p

