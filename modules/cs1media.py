#
# cs1media.py
#
# Environment for manipulating Images 
#
# 2010/03/24 Otfried Cheong
# 2010/09/02: Convert image to RGB on loading
#
# Inspired and using some code from picture.py by Mark Guzdial.
#
# On Linux, need packages python-tk, python-imaging-tk
#

import sys as _sys
import Image as _Image
import ImageTk as _ImageTk
import easygui as _easygui
import tkColorChooser as _tkColorChooser
import tkFont as _tkFont
import Tkinter as _Tk

# --------------------------------------------------------------------

class Picture(object):
  """A digital image."""

  def __init__(self, surf):
    """Create a Picture from an Image object."""
    self._title = ""
    self._reset(surf)

  def _reset(self, surf):
    self._surf = surf
    self._pixels = surf.load()

  def size(self):
    """Return size of the image as a tuple (width, height)."""
    return self._surf.size

  def show1(self):
    """Display the image."""
    self._surf.show()

  def show(self):
    """Display the image and wait until user closes the image window."""
    tool = PictureTool(self)
    tool.run_tool()

  def set_pixels(self, color = (0,0,0)):
    """Set all pixels of the image to the given color."""
    surf = _Image.new("RGB", self._surf.size, color)
    self._reset(surf)

  def set_title(self, title):
    """Set title of image."""
    self._title = title

  def title(self):
    """Return title of image."""
    return self._title

  def get(self, x, y):
    """Return pixel at x, y."""
    return self._pixels[x, y]

  def set(self, x, y, color):
    """Set pixel at x, y to color."""
    self._pixels[x, y] = color

  def save_as(self, filename = None):
    """Save image as filename.
    If no filename is given, open file-chooser."""
    if not filename:
      filename = _easygui.filesavebox("Save image as", _sys.argv[0], 
                                      "unnamed.png",
                                      [ [ "*.jpg", "*.png", "*.bmp",
                                          "Image files" ] ])
      if not filename: 
        raise RuntimeError("No file name provided for saving.")
    self._surf.save(filename)

# --------------------------------------------------------------------

def create_picture(width, height, color = (0,0,0)):
  """Create an image of size width x height, and fill with color."""
  if width < 0 or height < 0:
    raise ValueError("Invalid image dimensions: " + str(width) + ", " 
                     + str(height))
  p = Picture(_Image.new("RGB", (width, height), color))
  return p

def load_picture(filename = None):
  """Create an image by loading file filename.
  Opens file-chooser if no file name given."""
  if not filename:
    filename = _easygui.fileopenbox("Select an image", 
                                    _sys.argv[0], '*', 
                                    [ [ "*.jpg", "*.png", "*.bmp", "*.gif",
                                        "Image files" ] ])
    if not filename: 
      raise RuntimeError("No image file selected.")
  img = _Image.open(filename)
  if img.mode != "RGB":
    img = img.convert("RGB")
  p = Picture(img)
  p.set_title(filename)
  return p

def choose_color():
  color = _tkColorChooser.askcolor()
  new_color = (color[0][0], color[0][1], color[0][2])
  return new_color

# --------------------------------------------------------------------

##
## Color Constants
##

class Color(object):
  """Definitions for many beautiful colors."""

  aliceblue = (240, 248, 255)
  antiquewhite = (250, 235, 215)
  aqua = (0, 255, 255)
  aquamarine = (127, 255, 212)
  azure = (240, 255, 255)
  beige = (245, 245, 220)
  bisque = (255, 228, 196)
  black = (0, 0, 0)
  blanchedalmond = (255, 235, 205)
  blue = (0, 0, 255)
  blueviolet = (138, 43, 226)
  brown = (165, 42, 42)
  burlywood = (222, 184, 135)
  cadetblue = (95, 158, 160)
  chartreuse = (127, 255, 0)
  chocolate = (210, 105, 30)
  coral = (255, 127, 80)
  cornflowerblue = (100, 149, 237)
  cornsilk = (255, 248, 220)
  crimson = (220, 20, 60)
  cyan = (0, 255, 255)
  darkblue = (0, 0, 139)
  darkcyan = (0, 139, 139)
  darkgoldenrod = (184, 134, 11)
  darkgray = (169, 169, 169)
  darkgreen = (0, 100, 0)
  darkkhaki = (189, 183, 107)
  darkmagenta = (139, 0, 139)
  darkolivegreen = (85, 107, 47)
  darkorange = (255, 140, 0)
  darkorchid = (153, 50, 204)
  darkred = (139, 0, 0)
  darksalmon = (233, 150, 122)
  darkseagreen = (143, 188, 143)
  darkslateblue = (72, 61, 139)
  darkslategray = (47, 79, 79)
  darkturquoise = (0, 206, 209)
  darkviolet = (148, 0, 211)
  deeppink = (255, 20, 147)
  deepskyblue = (0, 191, 255)
  dimgray = (105, 105, 105)
  dodgerblue = (30, 144, 255)
  firebrick = (178, 34, 34)
  floralwhite = (255, 250, 240)
  forestgreen = (34, 139, 34)
  fuchsia = (255, 0, 255)
  gainsboro = (220, 220, 220)
  ghostwhite = (248, 248, 255)
  gold = (255, 215, 0)
  goldenrod = (218, 165, 32)
  gray = (128, 128, 128)
  green = (0, 128, 0)
  greenyellow = (173, 255, 47)
  honeydew = (240, 255, 240)
  hotpink = (255, 105, 180)
  indianred = (205, 92, 92)
  indigo = (75, 0, 130)
  ivory = (255, 255, 240)
  khaki = (240, 230, 140)
  lavender = (230, 230, 250)
  lavenderblush = (255, 240, 245)
  lawngreen = (124, 252, 0)
  lemonchiffon = (255, 250, 205)
  lightblue = (173, 216, 230)
  lightcoral = (240, 128, 128)
  lightcyan = (224, 255, 255)
  lightgoldenrodyellow = (250, 250, 210)
  lightgreen = (144, 238, 144)
  lightgrey = (211, 211, 211)
  lightpink = (255, 182, 193)
  lightsalmon = (255, 160, 122)
  lightseagreen = (32, 178, 170)
  lightskyblue = (135, 206, 250)
  lightslategray = (119, 136, 153)
  lightsteelblue = (176, 196, 222)
  lightyellow = (255, 255, 224)
  lime = (0, 255, 0)
  limegreen = (50, 205, 50)
  linen = (250, 240, 230)
  magenta = (255, 0, 255)
  maroon = (128, 0, 0)
  mediumaquamarine = (102, 205, 170)
  mediumblue = (0, 0, 205)
  mediumorchid = (186, 85, 211)
  mediumpurple = (147, 112, 219)
  mediumseagreen = (60, 179, 113)
  mediumslateblue = (123, 104, 238)
  mediumspringgreen = (0, 250, 154)
  mediumturquoise = (72, 209, 204)
  mediumvioletred = (199, 21, 133)
  midnightblue = (25, 25, 112)
  mintcream = (245, 255, 250)
  mistyrose = (255, 228, 225)
  moccasin = (255, 228, 181)
  navajowhite = (255, 222, 173)
  navy = (0, 0, 128)
  oldlace = (253, 245, 230)
  olive = (128, 128, 0)
  olivedrab = (107, 142, 35)
  orange = (255, 165, 0)
  orangered = (255, 69, 0)
  orchid = (218, 112, 214)
  palegoldenrod = (238, 232, 170)
  palegreen = (152, 251, 152)
  paleturquoise = (175, 238, 238)
  palevioletred = (219, 112, 147)
  papayawhip = (255, 239, 213)
  peachpuff = (255, 218, 185)
  peru = (205, 133, 63)
  pink = (255, 192, 203)
  plum = (221, 160, 221)
  powderblue = (176, 224, 230)
  purple = (128, 0, 128)
  red = (255, 0, 0)
  rosybrown = (188, 143, 143)
  royalblue = (65, 105, 225)
  saddlebrown = (139, 69, 19)
  salmon = (250, 128, 114)
  sandybrown = (244, 164, 96)
  seagreen = (46, 139, 87)
  seashell = (255, 245, 238)
  sienna = (160, 82, 45)
  silver = (192, 192, 192)
  skyblue = (135, 206, 235)
  slateblue = (106, 90, 205)
  slategray = (112, 128, 144)
  snow = (255, 250, 250)
  springgreen = (0, 255, 127)
  steelblue = (70, 130, 180)
  tan = (210, 180, 140)
  teal = (0, 128, 128)
  thistle = (216, 191, 216)
  tomato = (255, 99, 71)
  turquoise = (64, 224, 208)
  violet = (238, 130, 238)
  wheat = (245, 222, 179)
  white = (255, 255, 255)
  whitesmoke = (245, 245, 245)
  yellow = (255, 255, 0)
  yellowgreen = (154, 205, 50)
  
# --------------------------------------------------------------------

class PictureTool:

  def __init__(self, pict):
    self.pict = pict
    
  def run_tool(self):
    self.root = _Tk.Tk()
    
    self.top = _Tk.Menu(self.root, bd=2)
    self.root.config(menu=self.top)
    
    self.zoom = _Tk.Menu(self.top, tearoff=0)
    self.zoom.add_command(label='25%', command=lambda : self.zoomf(0.25),
                          underline=0)
    self.zoom.add_command(label='50%', command=lambda : self.zoomf(0.5),
                          underline=0)
    self.zoom.add_command(label='75%', command=lambda : self.zoomf(0.75),
                          underline=0)
    self.zoom.add_command(label='100%', command=lambda : self.zoomf(1.0),
                          underline=0)
    self.zoom.add_command(label='150%', command=lambda : self.zoomf(1.5),
                          underline=0)
    self.zoom.add_command(label='200%', command=lambda : self.zoomf(2.0),
                          underline=0)
    self.zoom.add_command(label='400%', command=lambda : self.zoomf(4.0),
                          underline=0)
    self.zoom.add_command(label='800%', command=lambda : self.zoomf(8.0),
                          underline=0)
    
    self.top.add_cascade(label='Zoom', menu=self.zoom, underline=0)
    
    # create a frame and pack it
    self.frame1 = _Tk.Frame(self.root)
    self.frame1.pack(side=_Tk.BOTTOM, fill=_Tk.X)
    
    self.root.im = self.pict._surf
    self.root.zoomMult = 1.0
    
    self.root.photo1 = _ImageTk.PhotoImage(image=self.root.im)
    
    self.root.title(self.pict.title())
    
    # Canvas for the Image, with scroll bars
    
    self.canvas1 = _Tk.Canvas(self.frame1, width=self.root.photo1.width() -
                              1, height=self.root.photo1.height() - 1,
                              cursor="crosshair", borderwidth=0)
    self.root.vbar = _Tk.Scrollbar(self.frame1)
    self.root.hbar = _Tk.Scrollbar(self.frame1, orient='horizontal')
    self.root.vbar.pack(side=_Tk.RIGHT, fill=_Tk.Y)
    self.root.hbar.pack(side=_Tk.BOTTOM, fill=_Tk.X)
    
    self.canvas1.pack(side=_Tk.BOTTOM, padx=0, pady=0, anchor=_Tk.NW, 
                      fill=_Tk.BOTH, expand=_Tk.YES)

    # call on scroll move
    self.root.vbar.config(command=self.canvas1.yview)  
    self.root.hbar.config(command=self.canvas1.xview)
    # call on canvas move
    self.canvas1.config(yscrollcommand=self.root.vbar.set)  
    self.canvas1.config(xscrollcommand=self.root.hbar.set)
    self.draw_image(self.root.im)
    self.canvas1.bind('<Button-1>', self.canvClick)
    
    self.v = _Tk.StringVar()
    self.v.set("R:      G:      B:     ")
    self.xy = _Tk.StringVar()
    self.xy.set("X:      Y:      ")
    row = _Tk.Frame(self.root)
    font = _tkFont.Font(size=10)
    xyLabel = _Tk.Label(row, textvariable=self.xy, font=font)
    colorLabel = _Tk.Label(row, textvariable=self.v, font=font)
    self.canvas2 = _Tk.Canvas(row, width=35, bd=2, relief=_Tk.RIDGE, height=30)
    xyLabel.pack(side=_Tk.LEFT)
    colorLabel.pack(side=_Tk.LEFT, padx=100, pady=1)
    self.canvas2.pack(side=_Tk.LEFT, padx=2, pady=1)
    row.pack(side=_Tk.TOP, fill=_Tk.X)  # pack row on top

    # start the event loop
    self.root.mainloop()
      
  def zoomf(self, factor):
    # zoom in or out
    self.root.zoomMult = factor
    (wide, high) = self.root.im.size
    new = self.root.im.resize((int(wide * factor), int(high * factor)))
    self.draw_image(new)

  def draw_image(self, imgpil):
    self.root.photo1 = _ImageTk.PhotoImage(image=imgpil)  # not file=imgpath
    (scrwide, scrhigh) = self.root.maxsize()  # wm screen size x,y
    scrhigh -= 200  # leave room for top display/button at max photo size
    imgwide = self.root.photo1.width()  # size in pixels
    imghigh = self.root.photo1.height()  # same as imgpil.size
    
    fullsize = (0, 0, imgwide, imghigh)  # scrollable
    viewwide = min(imgwide, scrwide)  # viewable
    viewhigh = min(imghigh, scrhigh)
    
    self.canvas1.delete('all')  # clear prior photo
    self.canvas1.config(height=viewhigh, width=viewwide)  # viewable window size
    self.canvas1.config(scrollregion=fullsize)  # scrollable area size
    
    self.root.img = self.canvas1.create_image(0, 0, image=self.root.photo1,
                                              anchor=_Tk.NW)
    
    if imgwide <= scrwide and imghigh <= scrhigh:  # too big for display?
      self.root.state('normal')  # no: win size per img
    elif (_sys.platform)[:3] == 'win':
      # do windows fullscreen
      self.root.state('zoomed')  # others use geometry( )

  def canvClick(self, event):
    try:
      x = int(self.canvas1.canvasx(event.x) / self.root.zoomMult)
      y = int(self.canvas1.canvasy(event.y) / self.root.zoomMult)
      w, h = self.root.im.size
      if 0 <= x < w and 0 <= y < h:
        tk_rgb = "#%02x%02x%02x" % self.root.im.getpixel((x, y))
        self.canvas2.config(bg=tk_rgb)
        rgb = "R: %d; G: %d; B: %d;" % self.root.im.getpixel((x, y))
        self.v.set(rgb)
        xy = "X: %d; Y: %d;" % (x, y)
        self.xy.set(xy)
      else:
        rgb = "X,Y Out of Range"
        self.v.set(rgb)
    except ValueError:
      pass
    
def picture_tool(filename = None):
  """Allows you to find information about digital images.

  The PictureTool's Toolbar:

  Once you have opened an image, you can view information about its
  individual pixels by looking at the toolbar. To select a pixel drag
  (click and hold down) the mouse to the position you want and then
  release it to hold that position's information in the toolbar.

  The following information in the toolbar changes to reflect the
  properties of the pixel you selected:

  X = the x coordinate of the pixel (starting with 0, counting from the left) 
  Y = the y coordinate of the pixel (starting with 0, counting from the top)
  R = the Red value of the pixel (0 to 255)
  G = the Green value of the pixel (0 to 255)
  B = the Blue value of the pixel (0 to 255)

  In addition, the box at the far right displays the color of the pixel.

  Zooming in/out:
  To Zoom, select the amount of zoom you want from the zoom menu.
  Less than 100% zooms out and more than 100% zooms in. 
  The 100% zoom level will always return you to your orginal picture.
  
  filename: a string representing the location and name of picture.
  If no filename is given, a file-chooser opens."""

  if not filename:
    filename = _easygui.fileopenbox("Select an image", 
                                    _sys.argv[0], '*', 
                                    [ [ "*.jpg", "*.png", "*.bmp", "*.gif",
                                        "Image files" ] ])
    if not filename: 
      raise RuntimeError("No image file selected.")
  img = load_picture(filename)
  tool = PictureTool(img)
  tool.run_tool()

# --------------------------------------------------------------------
  
if __name__ == "__main__":
  if len(_sys.argv > 1):
    picture_tool(_sys.argv[1])
  else:
    picture_tool()

# --------------------------------------------------------------------
