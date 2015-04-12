#
# Display an animation of an elevator
#

import cs1graphics as _g
import threading as _threading
import time as _time

_canvas = None
_cabin = None
_ldoor = None
_rdoor = None
_cabin_delta = 0
_buttons = [ None, None, None, None ]
_button_state = [ False, False, False, False ]
_lights = [ None, None, None, None ]
_timer = None

# --------------------------------------------------------------------

class ElevatorError(Exception):
  def __init__(self, str):
    Exception.__init__(self, str)

class Button(_g.Polygon, _g.EventHandler):
  """A button that can respond to events."""
  def __init__(self, id, up):
    """Create a new button with id and direction up (True or False)."""
    _g.Polygon.__init__(self, _g.Point(-15,15), _g.Point(15,15), 
                        _g.Point(0,-15))
    _g.EventHandler.__init__(self)
    self._baseBorderWidth = self._borderWidth
    self.setFillColor('white')
    self._id = id
    self.addHandler(self)
    self.adjustReference(15,-15)
    if not up:
      self.flip(90)
  
  def _noAutomaticCall(self):
    pass
  
  def handle(self, event):
    """Highlight the button when the button is clicked."""
    if event._eventType == 'mouse click':
      _g.Polygon.setBorderWidth(self, self._baseBorderWidth + 2)
      _g.Polygon.setFillColor(self, 'gray')
      _handle_button(self._id, True)
    elif event._eventType == 'mouse release':
      _g.Polygon.setBorderWidth(self, self._baseBorderWidth)
      _g.Polygon.setFillColor(self, 'white')
      _handle_button(self._id, False)

  def setBorderWidth(self, width):
    """
    Set the width of the border to the indicated width.
    """
    self._baseBorderWidth = width
    _g.Polygon.setBorderWidth(self, width)
    
# --------------------------------------------------------------------

def _handle_button(id, state):
  global _button_state
  #print "Button #", id, "changed state to", state
  _button_state[id] = state

def _cabin_step():
  _cabin.move(0, _cabin_delta * 5)
  y = _cabin.getReferencePoint().getY()
  if y < 0:
    raise ElevatorError("Elevator jumped off the roof and exploded.")
  if y > 700:
    raise ElevatorError("Elevator reached core of Earth and melted.")
  _set_timer()

def _set_timer():
  global _timer
  if _timer:
    _timer.cancel()
  if _cabin_delta != 0:
    _timer = _threading.Timer(0.1, _cabin_step)
    _timer.start()
  
# --------------------------------------------------------------------

def init_hardware():
  global _canvas, _cabin, _ldoor, _rdoor
  _canvas = _g.Canvas(200, 600)
  _canvas.setBackgroundColor("lightblue")
  _canvas.setTitle("Elevator")
  r = _g.Rectangle(90, 160)
  r.setFillColor("yellow")
  r.setBorderColor("red")
  _ldoor = _g.Rectangle(40, 150)
  _rdoor = _g.Rectangle(40, 150)
  _ldoor.move(-20, 0)
  _rdoor.move(20, 0)
  _ldoor.adjustReference(-20, 0)
  _rdoor.adjustReference(20, 0)
  _ldoor.setFillColor("blue")
  _rdoor.setFillColor("blue")
  r.setDepth(60)
  _cabin = _g.Layer()
  _cabin.add(r)
  _cabin.add(_ldoor)
  _cabin.add(_rdoor)
  _cabin.moveTo(70, 600 - 90)
  _canvas.add(_cabin)
  for i in range(3):
    floor = _g.Rectangle(70, 6)
    floor.setFillColor("blue")
    floor.moveTo(150, 600 - i * 200 - 13)
    _canvas.add(floor)
  for i in range(4):
    floor = (i + 1)//2
    button = Button(i, ((i % 2) == 0))
    button.moveTo(150, 600 - floor * 200 - 50)
    light = _g.Circle(10)
    light.moveTo(150, 600 - floor * 200 - 90)
    light.setFillColor("darkblue")
    if i == 1:
      button.move(15,0)
      light.move(15,0)
    elif i == 2:
      button.move(-15,0)
      light.move(-15,0)
    _canvas.add(button)
    _canvas.add(light)
    _buttons[i] = button
    _lights[i] = light

# --------------------------------------------------------------------

def open_door():
  """Open cabin doors."""
  if _ldoor.getWidth() < 40:
    raise RuntimeError("Door is already open")
  for w in range(39, 5, -2):
    _ldoor.setWidth(w)
    _rdoor.setWidth(w)

def close_door():
  if _ldoor.getWidth() == 40:
    raise RuntimeError("Door is already closed")
  for w in range(6, 41, 2):
    _ldoor.setWidth(w)
    _rdoor.setWidth(w)

# --------------------------------------------------------------------

def set_motor(speed):
  global _cabin_delta
  if speed > 0:
    _cabin_delta = -1
  elif speed < 0:
    _cabin_delta = 1
  else:
    _cabin_delta = 0
  _set_timer()

# --------------------------------------------------------------------

def set_light(light, state):
  """Turn light on or off. Lights are numbered 0 .. 3."""
  if light < 0 or light > 3:
    raise ValueError("Illegal light number")
  if state:
    col = "yellow"
  else:
    col = "darkblue"
  _lights[light].setFillColor(col)

# --------------------------------------------------------------------

def get_button(num):
  """Returns True if button num is now pressed.
  Buttons are numbered 0 .. 3."""
  if num < 0 or num > 3:
    raise ValueError("Illegal button number")
  _time.sleep(0.01)
  return _button_state[num]

# --------------------------------------------------------------------

def get_sensor(floor):
  """Returns true if cabin is at given floor.
  Floors are numbered 1 .. 3."""
  if floor < 1 or floor > 3:
    raise ValueError("Illegal floor")
  _time.sleep(0.01)
  y = 800 - 200 * floor - 90
  return _cabin.getReferencePoint().getY() == y

# --------------------------------------------------------------------
