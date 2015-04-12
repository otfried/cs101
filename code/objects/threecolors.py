from cs1media import *

high = 180
low = 60

yellow = (255, 255, 0)
dark = (0, 0, 128)
green = (0, 160, 0)

img = load_picture("../photos/yuna1.jpg")

w, h = img.size()
for y in range(h):
  for x in range(w):
    r, g, b = img.get(x, y)
    v = (r + g + b) // 3
    if v > high:
      img.set(x, y, yellow)
    elif v > low:
      img.set(x, y, green)
    else:
      img.set(x, y, dark)

img.show()
img.save_as("threecolors.jpg")

