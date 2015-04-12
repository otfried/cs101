#
# cs1robots.py
#
# Environment for steering a robot through a grid world
# for learning to program in Python
#
# Inspired by and using code from RUR-PLE by Andre Roberge
#
# 2010/01/14 Otfried Cheong
# 2010/02/23: Changed to refresh only once after every move
# 2010/02/24: Fixed refresh in world editing.
# 2010/08/12: Improved handling of beepers to speed up.
#
# On Linux, need packages python-tk, python-imaging-tk
#

import sys as _sys
import cs1graphics as _g
import easygui as _easygui
import re as _re
import time as _time

from cs1robots_images import _robot_images

# PIL isn't actually used in cs1robots, but is needed to use
# cs1graphics properly.  So we make sure it is there, as otherwise
# users get a confusing error message.
import Image as _Image
import ImageDraw as _ImageDraw
import ImageTk as _ImageTk

#_g._debug = 2

_scene = None
_world = None

_directions = [ (0, 1), (-1, 0), (0, -1), (1, 0) ]
_orient_dict = { 'E': 3, 'S': 2, 'W': 1, 'N': 0}

class RobotError(Exception):
  def __init__(self, str):
    Exception.__init__(self, str)

def pause(delay = 1.0):
  """Pause for delay seconds."""
  _time.sleep(delay)

# --------------------------------------------------------------------

class _Beeper(object):
  """One ore more beepers at a crossing in the world."""
  def __init__(self, radius, av, st, num = 1):
    self.av = av
    self.st = st
    self.num = num
    self.layer = _g.Layer()
    self.circle = _g.Circle(radius = radius)
    self.text = _g.Text("%d" % num, 11, _g.Point(0, 0))
    self.layer.add(self.circle)
    self.layer.add(self.text)
    self.circle.setFillColor("yellow")
    self.circle.setBorderColor("orange")
    self.circle.setDepth(10)
    self.text.setDepth(5)
    self.layer.setDepth(5)

  def set_number(self, num):
    self.num = num
    self.text.setMessage("%d" % num)
    
class _World(object):
  """This class defines the world's logic."""

  def __init__(self, avenues = 10, streets = 10, walls = [], beepers = {}):
    self.av = avenues
    self.st = streets
    self.num_cols = 2*avenues + 1
    self.num_rows = 2*streets + 1
    self.walls = walls
    for (col, row) in self.walls:
      if not (col+row) % 2:
        raise RuntimeError("Wall in impossible position (%d, %d)." % (col,row))
    self.beepers = beepers
    self.borders = []
    self.beeper_icons = {}
    self.set_borders()

  def cr2xy(self, col, row):
    x = self.left + self.ts * col
    y = self.bottom - self.ts * row
    return x, y

  def set_borders(self):
    """The world is surrounded by a continuous wall.  This function
       sets the corresponding "wall" or "border" based on the world's
       dimensions."""
    for col in range(1, self.num_cols-1, 2):
      if (col, 0) not in self.borders:
        self.borders.append( (col, 0) )
      if (col, self.num_rows) not in self.borders:
        self.borders.append( (col, self.num_rows-1) )
      for row in range(1, self.num_rows-1, 2):
        if (0, row) not in self.borders:
          self.borders.append( (0, row) )
        if (self.num_cols, row) not in self.borders:
          self.borders.append( (self.num_cols-1, row) )

  def toggle_wall(self, col, row):
    """This function is intended for adding or removing a
       wall from a GUI world editor."""
    if (col+row) % 2 :  # safety check
      if (col, row) in self.walls: # toggle value
        self.walls.remove((col, row))
      else:
        self.walls.append((col, row))
    else:
      raise RuntimeError("Wall in impossible position (%d, %d)." % (col,row))

  def is_clear(self, col, row):
    """Returns True if there is no wall or border here."""
    return not ((col, row) in self.walls or
                (col, row) in self.borders)
  
  def add_beeper(self, av, st):
    """Add a single beeper."""
    assert self.layer
    if (av, st) in self.beepers:
      self.beepers[(av, st)] += 1
      bp = self.beeper_icons[(av,st)]
      bp.set_number(self.beepers[(av, st)])
    else:
      self.beepers[(av, st)] = 1
      self._create_beeper(av, st)

  def remove_beeper(self, av, st):
    """Remove a beeper (does nothing if no beeper here)."""
    assert self.layer
    if (av, st) in self.beepers:
      self.beepers[(av, st)] -= 1
      if self.beepers[(av, st)] == 0:
        del self.beepers[(av, st)]
        self.layer.remove(self.beeper_icons[(av,st)].layer)
        del self.beeper_icons[(av,st)]
      else:
        bp = self.beeper_icons[(av,st)]
        bp.set_number(self.beepers[(av, st)])

  def _create_beeper(self, av, st):
    num = self.beepers[(av, st)]
    bp = _Beeper(0.6 * self.ts, av, st, num)
    x, y = self.cr2xy(2 * av - 1, 2 * st - 1)
    bp.layer.moveTo(x, y)
    self.beeper_icons[(av, st)] = bp
    self.layer.add(bp.layer)

  def create_layer(self):
    # compute tilesize and border coordinates
    w, h = _scene.getWidth(), _scene.getHeight()
    tsx =  w / (self.num_cols + 2)
    tsy =  h / (self.num_rows + 2)
    self.ts = min(tsx, tsy)
    self.left = 2 * self.ts
    self.right = self.left + 2 * self.ts * self.av
    self.bottom = h - 2 * self.ts
    self.top = self.bottom - 2 * self.ts * self.st
    self.layer = _g.Layer()
    # Create avenues
    for av in range(self.av):
      x = self.left + self.ts * (2 * av + 1) 
      l = _g.Path([_g.Point(x, self.top), _g.Point(x, self.bottom)])
      l.setBorderColor("light gray")
      self.layer.add(l)
      self.layer.add(_g.Text("%d" % (av + 1), 10, 
                             _g.Point(x, self.bottom + self.ts)))
    # Create streets
    for st in range(self.st):
      y = self.bottom - self.ts * (2 * st + 1) 
      l = _g.Path([_g.Point(self.left, y), _g.Point(self.right, y)])
      l.setBorderColor("light gray")
      self.layer.add(l)
      self.layer.add(_g.Text("%d" % (st + 1), 10, 
                             _g.Point(self.left - self.ts, y)))
    # Create border
    border = _g.Polygon(_g.Point(self.left, self.bottom),
                        _g.Point(self.right, self.bottom),
                        _g.Point(self.right, self.top),
                        _g.Point(self.left, self.top))
    border.setBorderWidth(5)
    border.setBorderColor("dark red")
    border.setDepth(10)
    self.layer.add(border)
    # Create walls
    for (col, row) in self.walls:
      if col % 2 == 0:  # vertical wall
        x1, y1 = self.cr2xy(col, row - 1)
        x2, y2 = self.cr2xy(col, row + 1)
      else: # horizontal wall
        x1, y1 = self.cr2xy(col - 1, row)
        x2, y2 = self.cr2xy(col + 1, row)
      w = _g.Path([_g.Point(x1,y1), _g.Point(x2,y2)])
      w.setBorderWidth(5)
      w.setBorderColor("dark red")
      w.setDepth(10)
      self.layer.add(w)
    # Create beepers
    for (av, st) in self.beepers:
      self._create_beeper(av, st)
    # Layer finished
    _scene.add(self.layer)
    
  def update_layer(self):
    _scene.remove(self.layer)
    self.beeper_icons = {}
    self.create_layer()

  def save(self, out):
    av_string = "avenues = " + str(self.av) + '\n'
    st_string = "streets = " + str(self.st) + '\n'
    if len(self.walls) > 0:
      wall_string = "walls = [\n"
      for item in self.walls:
        wall_string += ("    " + str(item) + ', \n')
      wall_string = wall_string[:-3] + '\n]\n'
    else:
      wall_string = "walls = []\n"
    if len(self.beepers) > 0:
      beeper_string = "beepers = {\n"
      for key in self.beepers:
        beeper_string += ("    " + str(key) + ': ' +
                          str(self.beepers[key]) + ', \n')
      beeper_string = beeper_string[:-3] + '\n}\n'
    else:
      beeper_string = "beepers = {}\n"
    out.write(av_string + st_string + wall_string + beeper_string)
    
# --------------------------------------------------------------------

def create_world(avenues = 10, streets = 10):
  """Create an empty robot world."""
  global _scene, _world
  if _scene:
    raise RuntimeError("A robot world already exists!")
  _scene = _g.Canvas()
  _scene.setWidth(50 * avenues)
  _scene.setHeight(50 * streets)
  _scene.setTitle("Robot World")
  _world = _World(avenues, streets)
  _world.create_layer()
  _scene.setAutoRefresh(False)

def _check_world(contents):
  # safety check
  safe = contents[:]
    # only allow known keywords
  keywords = ["avenues", "streets", "walls", "beepers", "robot",
              "'s'", "'S'", '"s"', '"S"',
              "'e'", "'E'", '"e"', '"E"',
              "'w'", "'W'", '"w"', '"W"',
              "'n'", "'N'", '"n"', '"N"', ]
  for word in keywords:
    safe = safe.replace(word, '')
  safe = list(safe)
  for char in safe:
    if char.isalpha():
      raise ValueError("Invalid word or character in world file")
    
def load_world(filename = None):
  """Loads a robot world from filename.
  Opens file-chooser if no filename is given."""
  global _scene, _world
  if _scene:
    raise RuntimeError("A robot world already exists!")
  if not filename:
    filename = _easygui.fileopenbox("Select a Robot world", 
                                    "Robot World", '*', [ "*.wld" ])
    if not filename: 
      raise RuntimeError("No world file selected.")
  txt = open(filename, 'rb').read()
  txt = _re.sub('\r\n', '\n', txt) # Windows
  txt = _re.sub('\r', '\n', txt)  # Mac
  _check_world(txt)
  wd = {}
  # extracts avenues, streets, walls and beepers
  try:
    exec txt in wd
    w = _World(wd['avenues'], wd['streets'], wd['walls'], wd['beepers'])
  except:
    raise ValueError("Error interpreting world file.")
  _world = w
  _scene = _g.Canvas()
  _scene.setWidth(50 * w.av)
  _scene.setHeight(50 * w.st)
  i = filename.rfind("/")
  if i >= 0: filename = filename[i+1:]
  _scene.setTitle("Robot World: " + filename)
  _world.create_layer()
  _scene.setAutoRefresh(False)

def save_world(filename = None):
  """Save a robot world to filename.
  Opens file-chooser if no filename is given."""
  if not filename:
    filename = _easygui.filesavebox("Select a Robot world", 
                                    "Robot World", '*', [ "*.wld" ])
    if not filename: 
      raise RuntimeError("No world file selected.")
  out = open(filename, "w")
  _world.save(out)
  out.close()

def edit_world():
  """Edit the current robot world.
  You can add and remove walls by clicking at the wall position.
  Add a beeper by clicking with the left button at an intersection.
  Remove a beeper with the right mouse button."""
  while True:
    e = _scene.wait()
    d = e.getDescription()
    if d == "canvas close":
      _sys.exit(1)
    if d == "keyboard" and e.getKey() in [ '\r', '\n' ]:
      return
    if d == "mouse click":
      x = int(e.getMouseLocation().getX())
      y = int(e.getMouseLocation().getY())
      print "Mouse button", e.getButton(), "at", (x, y)
      col = (x - _world.left + _world.ts / 2) / _world.ts
      row = (_world.bottom - y + _world.ts / 2) / _world.ts
      if (col % 2) == 1 and (row % 2) == 1:
        print "corner"
        # corner
        av = (col + 1) / 2
        st = (row + 1) / 2
        if av < 1 or av > _world.av or st < 1 or st > _world.st:
          continue
        if e.getButton() == 1:
          print "add beeper"
          _world.add_beeper(av, st)
          _scene.refresh()
        elif e.getButton() == 3:
          print "remove beeper"
          _world.remove_beeper(av, st)
          _scene.refresh()
      elif ((col + row) % 2) == 1:
        # wall position
        print "wall position"
        if (col < 1 or col >= _world.num_cols - 1 or
            row < 1 or row >= _world.num_rows - 1):
          continue
        _world.toggle_wall(col, row)
        _world.update_layer()
        _scene.refresh()
  
# --------------------------------------------------------------------

class Robot(object):

  def __init__(self, color = "gray", orientation = 'E', beepers = 0,
               avenue = 1, street = 1):
    """Create a new robot."""
    if not color in _robot_images:
      raise TypeError('color must be a color name')
    self._image = [ None, None, None, None ]
    for i in range(4):
      self._image[i] = _g.Image("base64:" + _robot_images[color][i])
      self._image[i].moveTo(-100, -100)
      self._image[i].setDepth(0)
      _scene.add(self._image[i])
    self._dir = _orient_dict[orientation]
    self._x = avenue
    self._y = street
    self._beeper_bag = beepers
    self._trace = None
    self._delay = 0
    self._steps = 0
    self._update_pos()
    _scene.refresh()

  def _update_pos(self):
    x, y  = _world.cr2xy(2 * self._x - 1, 2 * self._y - 1)
    self._image[self._dir].moveTo(x, y)

  def _trace_pos(self):
    x, y  = _world.cr2xy(2 * self._x - 1, 2 * self._y - 1)
    xr, yr =  _directions[(self._dir - 1) % 4]
    xb, yb =  _directions[(self._dir - 2) % 4]
    return x + 5 * (xr + xb), y - 5 * (yr + yb)

  def _update_trace(self):
    if self._trace:
      x, y = self._trace_pos()
      self._trace.addPoint(_g.Point(x, y))

  def _refresh(self):
    _scene.refresh()
      
  def __del__(self):
    if _scene:
      for i in range(4):
        _scene.remove(self._image[i])

# --------------------------------------------------------------------

  def set_trace(self, color = None):
    """Without color argument, turn off tracing.
With color argument, start a new trace in that color."""
    if not color:
      if self._trace:
        _scene.remove(self._trace)
      self._trace = None
    else:
      x, y  = self._trace_pos()
      self._trace = _g.Path([_g.Point(x, y)])
      self._trace.setBorderColor(color)
      _scene.add(self._trace)

  def set_pause(self, delay = 0):
    """Set a pause to be made after each move."""
    self._delay = delay

# --------------------------------------------------------------------

  def get_pos(self):
    """Returns current robot position."""
    return self._x, self._y

  def turn_left(self):
    """Rotate left by 90 degrees."""
    self._image[self._dir].moveTo(-100, -100)
    self._dir = (self._dir + 1) % 4
    self._update_pos()
    self._update_trace()
    self._refresh()

  def move(self):
    """Move one street/avenue in direction where robot is facing."""
    if self.front_is_clear():
      xx, yy = _directions[self._dir]
      self._x += xx
      self._y += yy
    else:
      raise RobotError("That move really hurt!\n Please, make sure that " + 
                       "there is no wall in front of me!""")
    self._update_pos()
    self._update_trace()
    self._refresh()
    if self._delay > 0:
      _time.sleep(self._delay)
    
  def front_is_clear(self):
    """Returns True if no wall or border in front of robot."""
    col = 2 * self._x - 1
    row = 2 * self._y - 1
    xx, yy = _directions[self._dir]
    return _world.is_clear(col + xx, row + yy)

  def left_is_clear(self):
    """Returns True if no walls or borders are to the immediate left
    of the robot."""
    col = 2 * self._x - 1
    row = 2 * self._y - 1
    xx, yy = _directions[(self._dir + 1) % 4]
    return _world.is_clear(col + xx, row + yy)

  def right_is_clear(self):
    """Returns True if no walls or borders are to the immediate right
    of the robot."""
    col = 2 * self._x - 1
    row = 2 * self._y - 1
    xx, yy = _directions[(self._dir - 1) % 4]
    return _world.is_clear(col + xx, row + yy)

  def facing_north(self):
    """Returns True if Robot is facing north."""
    return (self._dir == 0)

  def carries_beepers(self):
    """Returns True if some beepers are left in Robot's bag."""
    return (self._beeper_bag > 0)

  def on_beeper(self):
    """Returns True if beepers are present at current robot position."""
    return ((self._x, self._y) in _world.beepers)

  def pick_beeper(self):
    """Robot picks one beeper up at current location."""
    if self.on_beeper():
      _world.remove_beeper(self._x, self._y)
      self._refresh()
      self._beeper_bag += 1
    else:
      raise RobotError("I must be on a beeper to pick it up.")

  def drop_beeper(self):
    """Robot drops one beeper down at current location."""
    if self.carries_beepers():
      self._beeper_bag -= 1
      _world.add_beeper(self._x, self._y)
      self._refresh()
    else:
      raise RobotError("I am not carrying any beepers.")

# --------------------------------------------------------------------

if __name__ == "__main__":
  if len(_sys.argv) > 1:
    load_world(_sys.argv[1])
  else:
    create_world(24, 14)
  edit_world()
  r = Robot("yellow")
  r.set_trace("blue")
  while True:
    try:
      e = _scene.wait()
      d = e.getDescription()
      if d == "canvas close":
        break
      if d == "keyboard":
        k = e.getKey()
        if k == "q":
          _scene.close()
          break
        elif k == " ":
          try:
            r.move()
          except:
            _easygui.msgbox("OUCH!")
        elif k == "t":
          r.turn_left()
        elif k == "w":
          load_world()
        elif k == "p":
          r.pick_beeper()
        elif k == "d":
          r.drop_beeper()
    except:
      _easygui.exceptionbox()

# --------------------------------------------------------------------
