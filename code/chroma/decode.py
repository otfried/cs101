
from cs1media import *

def decode(img):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      if r % 2 != 0: 
        img.set(x, y, Color.black)
      else:
        img.set(x, y, Color.white)

img = load_picture("secret1.png")
decode(img)
img.show()

