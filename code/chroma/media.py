from cs1media import *
import math
import random

def make_lighter(img, factor):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      r = int(factor * r)
      g = int(factor * g)
      b = int(factor * b)
      if r > 255: r = 255
      if g > 255: g = 255
      if b > 255: b = 255
      img.set(x, y, (r, g, b))

def make_redder(img, factor):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      g = int(factor * g)
      b = int(factor * b)
      img.set(x, y, (r, g, b))

def negative(img):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      r, g, b = 255 - r, 255 - g, 255 - b
      img.set(x, y, (r, g, b))

def bw(img):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      v = luminance(img.get(x, y))
      img.set(x, y, (v, v, v))

def twolevels(img, threshold):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      v = luminance(img.get(x, y))
      if v > threshold:
        img.set(x, y, Color.white)
      else:
        img.set(x, y, Color.black)

def sepia(img):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      v = int(0.299 * r + 0.587 * g + 0.114 * b)
      r, g, b = v, v, v
      if v < 63:
        r = int(1.1 * r)
        b = int(0.9 * b)
      elif 63 <= v < 192:
        r = int(1.15 * r)
        b = int(0.85 * b)
      elif 192 <= v:
        r = int(1.08 * r)
        b = int(0.93 * b)
      if r > 255: r = 255
      img.set(x, y, (r, g, b))

def prison(img, step):
  w, h = img.size()
  for y in range(0, h, step):
    for x in range(w):
      img.set(x, y, (0, 0, 0))

def mirror(img):
  w, h = img.size()
  for y in range(0, h):
    for x in range(w / 2):
      pl = img.get(x, y)
      pr = img.get(w - x - 1, y)
      img.set(x, y, pr)
      img.set(w - x - 1, y, pl)

def reflect(img, x0, ltr = True):
  w, h = img.size()
  w0 = min(x0, w-x0-1)
  for y in range(0, h):
    for x in range(w0):
      if ltr:
        pl = img.get(x0 - x, y)
        img.set(x0 + x, y, pl)
      else:
        pr = img.get(x0 + x, y)
        img.set(x0 - x, y, pr)

def interpolate(t, c1, c2):
  r1, g1, b1 = c1
  r2, g2, b2 = c2
  r = int((1-t) * r1 + t * r2)
  g = int((1-t) * g1 + t * g2)
  b = int((1-t) * b1 + t * b2)
  return (r, g, b)

def gradient(img, c1, c2):
  w, h = img.size()
  for y in range(h):
    t = float(y) / (h-1) # 0 .. 1
    p = interpolate(t, c1, c2)
    for x in range(w):
      img.set(x, y, p)

def concat(imglist):
  # compute height and width
  w = 0
  h = 0
  for img in imglist:
    w1, h1 = img.size()
    w += w1
    h = max(h, h1)
  r = create_picture(w, h, Color.white)
  x0 = 0
  for img in imglist:
    w1, h1 = img.size()
    for y in range(h1):
      for x in range(w1):
        r.set(x0 + x, y, img.get(x, y))
    x0 += w1
  return r

def statue():
  img1 = load_picture("photos/statue.jpg")
  bw(img1)
  img2 = load_picture("photos/statue.jpg")
  sepia(img2)
  r = concat([img1, img2])
  r.show()
  r.save_as("statue_bw_sepia.jpg")

def yuna():
  l = []
  for i in range(3):
    l.append(load_picture("photos/yuna2.jpg"))
  reflect(l[1], 65, True)
  reflect(l[2], 65, False)
  img = concat(l)
  img.show()
  img.save_as("yuna3.jpg")

def dist(c1, c2):
  r1, g1, b1 = c1
  r2, g2, b2 = c2
  return math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)

def chroma(img, key, threshold):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      p = img.get(x, y)
      if dist(p, key) < threshold:
        img.set(x, y, Color.yellow)

def blocks(img, step):
  w, h = img.size()
  for y in range(0, h - step, step):
    for x in range(0, w - step, step):
      # compute average
      r, g, b = 0, 0, 0
      for x0 in range(step):
        for y0 in range(step):
          r0, g0, b0 = img.get(x + x0, y + y0)
          r, g, b = r + r0, g + g0, b + b0
      norm = step * step
      r, g, b = r / norm, g / norm, b / norm
      for x0 in range(step):
        for y0 in range(step):
          img.set(x + x0, y + y0, (r, g, b))
  
def blocks_rect(img, step, x1, y1, x2, y2):
  w, h = img.size()
  for y in range(y1, y2 - step + 1, step):
    for x in range(x1, x2 - step + 1, step):
      # compute average
      r, g, b = 0, 0, 0
      for x0 in range(step):
        for y0 in range(step):
          r0, g0, b0 = img.get(x + x0, y + y0)
          r, g, b = r + r0, g + g0, b + b0
      norm = step * step
      r, g, b = r / norm, g / norm, b / norm
      for x0 in range(step):
        for y0 in range(step):
          img.set(x + x0, y + y0, (r, g, b))
  
def blur(img, radius):
  w, h = img.size()
  result = create_picture(w, h, Color.white)
  norm = (2 * radius + 1)**2
  for y in range(radius, h-radius):
    for x in range(radius, w-radius):
      # compute average
      r, g, b = 0, 0, 0
      for x0 in range(-radius,radius+1):
        for y0 in range(-radius,radius+1):
          r0, g0, b0 = img.get(x + x0, y + y0)
          r, g, b = r + r0, g + g0, b + b0
      r, g, b = r / norm, g / norm, b / norm
      result.set(x, y, (r, g, b))
  return result

def blur_rect(img, radius, x1, y1, x2, y2):
  w, h = img.size()
  result = create_picture(w, h)
  norm = (2 * radius + 1)**2
  for y in range(h):
    for x in range(w):
      if x1 <= x < x2 and y1 <= y < y2:
        # compute average
        r, g, b = 0, 0, 0
        for x0 in range(-radius,radius+1):
          for y0 in range(-radius,radius+1):
            r0, g0, b0 = img.get(x + x0, y + y0)
            r, g, b = r + r0, g + g0, b + b0
        r, g, b = r / norm, g / norm, b / norm
        result.set(x, y, (r, g, b))
      else:
        result.set(x, y, img.get(x, y))
  return result

def luminance(p):
  r, g, b = p
  return int(0.299 * r + 0.587 * g + 0.114 * b) 

def clone(img):
  """Make a copy of this image."""
  w, h = img.size()
  r = create_picture(w, h)
  for y in range(h):
    for x in range(w):
      r.set(x, y, img.get(x, y))
  return r

def edge_detect(img, threshold):
  w, h = img.size()
  r = create_picture(w, h)
  for y in range(1, h-1):
    for x in range(1, w-1):
      pl = luminance(img.get(x-1,y))
      pu = luminance(img.get(x,y-1))
      p = luminance(img.get(x,y))
      if (abs(pl - p) > threshold and
          abs(pu - p) > threshold):
        r.set(x, y, Color.black)
      else:
        r.set(x, y, Color.white)
  return r

def crop(img, x1, y1, x2, y2):
  w1 = x2 - x1
  h1 = y2 - y1
  r = create_picture(w1, h1)
  for y in range(h1):
    for x in range(w1):
      r.set(x, y, img.get(x1 + x, y1 + y))
  return r

def auto_left(img, key, tr):
  w, h = img.size()
  x = 0
  while x < w:
    for y in range(h):
      if dist(img.get(x, y), key) > tr:
        return x
    x += 1
  # all empty!
  return None
  
def auto_right(img, key, tr):
  w, h = img.size()
  x = w-1
  while x >= 0:
    for y in range(h):
      if dist(img.get(x, y), key) > tr:
        return x
    x -= 1
  # all empty!
  return None

def auto_up(img, key, tr):
  w, h = img.size()
  y = 0
  while y < h:
    for x in range(w):
      if dist(img.get(x, y), key) > tr:
        return y
    y += 1
  # all empty!
  return None
  
def auto_down(img, key, tr):
  w, h = img.size()
  y = h-1
  while y >= 0:
    for x in range(w):
      if dist(img.get(x, y), key) > tr:
        return y
    y -= 1
  # all empty!
  return None
  
def autocrop(img, threshold):
  w, h = img.size()
  key = img.get(0, 0)
  # remove boundary
  x1 = auto_left(img, key, threshold)
  x2 = auto_right(img, key, threshold)
  y1 = auto_up(img, key, threshold)
  y2 = auto_down(img, key, threshold)
  r = crop(img, x1, y1, x2, y2)
  return r

def rotate(img):
  h, w = img.size()
  r = create_picture(w, h)
  for y in range(h):
    for x in range(w):
      r.set(x, y, img.get(h - y - 1, x))
  return r

def scale_down(img, factor):
  w, h = img.size()
  w /= factor
  h /= factor
  result = create_picture(w, h)
  norm = factor ** 2
  for y in range(h):
    for x in range(w):
      # compute average
      r, g, b = 0, 0, 0
      x1 = x * factor
      y1 = y * factor
      for x0 in range(factor):
        for y0 in range(factor):
          r0, g0, b0 = img.get(x1 + x0, y1 + y0)
          r, g, b = r + r0, g + g0, b + b0
      r, g, b = r / norm, g / norm, b / norm
      result.set(x, y, (r, g, b))
  return result

#img = load_picture("photos/yuna4.jpg")
#blocks_rect(img, 4, 7, 300, 188, 392)
#r = blur_rect(img, 7, 7, 300, 188, 392)
def statue_chroma():
  r = load_picture("photos/statue.jpg")
  r1 = autocrop(r, 60)
  r2 = autocrop(r1, 200)
  w, h = r2.size()
  r3 = crop(r2, 1, 1, w-1, h-1)
  r4 = scale_down(r3, 2)
  chroma(r4, (41, 75, 146), 70)
  return r4
  #r3.show()
  #r3.save_as("statue_chroma.jpg")

def crop_geowi():
  img = load_picture("photos/geowi.jpg")
  r = crop(img, 67, 160, 237, 305)
  r.show()
  r.save_as("geowi_cropped.jpg")

def statue_autocrop():
  r = load_picture("photos/statue.jpg")
  r1 = autocrop(r, 60)
  r2 = autocrop(r1, 200)
  r2.show()
  r2.save_as("statue_cropped.jpg")

def paste(canvas, img, x1, y1):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      canvas.set(x1 + x, y1 + y, img.get(x, y))

def chroma_paste(canvas, img, x1, y1, key):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      p = img.get(x, y)
      if p != key:
        canvas.set(x1 + x, y1 + y, p)

def collage():
  trees = load_picture("photos/trees1.jpg")
  statue = statue_chroma()
  mirror(statue)
  chroma_paste(trees, statue, 200, 40, Color.yellow)
  trees.show()
  trees.save_as("collage2.jpg")
  
def concat_ex():
  geowi = load_picture("photos/geowi.jpg")
  statue = load_picture("photos/statue.jpg")
  yuna = load_picture("photos/yuna2.jpg")
  r = concat([geowi, statue, yuna])
  r.show()
  r.save_as("concat1.jpg")

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

def decode(img):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      r, g, b = img.get(x, y)
      if r % 2 != 0: 
        img.set(x, y, Color.black)
      else:
        img.set(x, y, Color.white)

def test2():  
  secret = load_picture("photos/yuna2.jpg")
  twolevels(secret, 128)
  img = load_picture("photos/trees1.jpg")
  encode(img, secret, 100, 100)
  img.save_as("secret1.png")

def find_closest(p, l):
  r = l[0]
  d = dist(p, l[0])
  for q in l:
    if dist(p, q) < d:
      r = q
      d = dist(p, q)
  return r

def random_color():
  return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

def posterize(img, color_list):
  w, h = img.size()
  for y in range(h):
    for x in range(w):
      p = img.get(x, y)
      img.set(x, y, find_closest(p, color_list))
      
def poster_test():
  img = load_picture("photos/yuna1.jpg")
  #color_list = [ Color.red, Color.blue, Color.green, Color.black, Color.white ]
  color_list = []
  for i in range(10):
    color_list.append(random_color())
  posterize(img, color_list)
  img.show()
  img.save_as("yuna_poster2.jpg")

# create blocks of value 0 to 255
def create_blocks(step):
  blocks = []
  for i in range(step ** 2 + 1):
    b = create_picture(step, step, Color.black)
    count = 0
    for x in range(step):
      for y in range(step):
        if count < i:
          b.set(x, y, Color.white)
        count += 1
    blocks.append(b)
  return blocks
  
def newspaper(img):
  step = 4
  blocks = create_blocks(step)
  nb = len(blocks)  # 0 --> 0, 255 -> nb - 1
  w, h = img.size()
  r = create_picture(step * w, step * h)
  for y in range(h):
    for x in range(w):
      v = luminance(img.get(x, y))
      n = v * nb / 256
      paste(r, blocks[n], step * x, step * y)
  return r 

def news_test():
  img = load_picture("photos/yuna2.jpg")
  r = newspaper(img)
  r.show()
  r.save_as("yuna_newspaper.jpg")
  
news_test()
