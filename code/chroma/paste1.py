
from cs1media import *

def paste(canvas, img, x1, y1):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      canvas.set(x1 + x, y1 + y, img.get(x, y))

trees = load_picture("../photos/trees1.jpg")
statue = load_picture("../photos/statue1.jpg")
paste(trees, statue, 200, 50)
trees.show()

