
from cs1media import *

def luminance(p):
  r, g, b = p
  return int(0.299 * r + 0.587 * g + 0.114 * b) 

def encode(img, secret, x1, y1):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      if r % 2 != 0: 
        r -= 1
      img.set(x, y, (r, g, b))
  w1, h1 = secret.size()
  for y in range(h1):
    for x in range(w1):
      v = luminance(secret.get(x, y))
      r, g, b = img.get(x1 + x, y1 + y)
      if v < 128:
        r += 1
      img.set(x1 + x, y1 + y, (r, g, b))

secret = load_picture("../photos/yuna2.jpg")
img = load_picture("../photos/trees1.jpg")
encode(img, secret, 100, 100)
img.save_as("secret1.png")

