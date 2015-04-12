from cs1media import *

def luminance(p):
  r, g, b = p
  return int(0.299 * r + 0.587 * g + 0.114 * b) 

white = (255, 255, 255)
black = (0, 0, 0)

def blackwhite(img, threshold):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      v = luminance(img.get(x, y))
      if v > threshold:
        img.set(x, y, white)
      else:
        img.set(x, y, black)

img = load_picture("../photos/yuna1.jpg")
blackwhite(img, 100)
img.show()

