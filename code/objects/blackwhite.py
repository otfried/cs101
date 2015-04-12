from cs1media import *

threshold = 100
white = (255, 255, 255)
black = (0, 0, 0)

img = load_picture("../photos/yuna1.jpg")

w, h = img.size()
for y in range(h):
  for x in range(w):
    r, g, b = img.get(x, y)
    v = (r + g + b) // 3
    if v > threshold:
        img.set(x, y, white)
    else:
        img.set(x, y, black)

img.show()

