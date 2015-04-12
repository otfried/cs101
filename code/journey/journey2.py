#
# Journey of Chicken I
#
# Jeong-eun Yu and Geum-hyeon Song
# Version with Chicken objects by OC.
#

from cs1graphics import*

class Chicken(object):
  """Graphic representation of a chicken."""
  pass

def make_chicken(hen = False):
  layer = Layer()

  # Body
  if hen:
    body = Ellipse(70,80)
    body.setFillColor("white")
  else:
    body = Ellipse(40,50)
    body.setFillColor("yellow")
    body.move(0, 10)
  body.setBorderColor("yellow")
  body.setDepth(20)
  layer.add(body)

  # Wing
  if hen:
    wing = Ellipse(60,40)
    wing.setFillColor("white")
    wing.setBorderColor("yellow")
    wing.move(15,20)
  else:
    wing = Ellipse(30,20)
    wing.setFillColor("yellow")
    wing.setBorderColor("orange")
    wing.move(10,25)
    wing.adjustReference(-5, -5)
  wing.setDepth(19)
  layer.add(wing)

  # Eye
  if hen:
    eye = Circle(3)
    eye.move(-15,-15)
  else:
    eye = Circle(2)
    eye.move(-5,0)
  eye.setFillColor("black")
  eye.setDepth(18)
  layer.add(eye)

  # Beak
  if hen:
    beak = Square(8)
    beak.move(-36,0)
  else:
    beak = Square(4)
    beak.move(-22,10)
  beak.rotate(45)
  beak.setFillColor("orange")
  beak.setBorderColor("orange")
  beak.setDepth(21)
  layer.add(beak)

  # Hen has two read dots on the head
  if hen:
    head1 = Ellipse(5, 8)
    head1.setFillColor("red")
    head1.setBorderColor("red")
    head1.move(0, -42)
    head1.setDepth(22)
    layer.add(head1)

    head2 = Ellipse(5, 8)
    head2.setFillColor("red")
    head2.setBorderColor("red")
    head2.move(-6, -42)
    head2.setDepth(22)
    layer.add(head2)

  # create Chicken object 
  ch = Chicken()
  ch.layer = layer
  ch.body = body
  ch.wing = wing
  ch.eye = eye

  # return the Chicken object
  return ch

canvas = Canvas(1000,300)
canvas.setBackgroundColor("light blue")
canvas.setTitle("Journey of Chicken")

ground = Rectangle(1000, 100)
ground.setFillColor("light green")
ground.move(500, 250)
canvas.add(ground)

sun = Circle(50)
sun.setFillColor("red")
sun.move(0,0)
canvas.add(sun)

hen = make_chicken(True)
chick1 = make_chicken()
chick1.layer.move(120,0)

herd = Layer()
herd.add(hen.layer)
herd.add(chick1.layer)
herd.move(600, 200)

chick2 = make_chicken()
chick2.layer.move(800,200)

canvas.add(herd)
canvas.add(chick2.layer)

for i in range(80):
  herd.move(-5, -2)
  herd.move(-5, 2)
  if i == 30:
    text1 = Text("OH!", 20)
    text1.move(800,160)
    canvas.add(text1)
  elif i == 40:
    canvas.remove(text1)
    text2 = Text("WHERE IS MY MOMMY GOING?", 30)
    text2.move(500,110)
    canvas.add(text2)
  elif i == 55:
    canvas.remove(text2)

for i in range(10):
  text3 = Text("Wait for ME~", 25)
  text3.move (500,110)
  canvas.add(text3)
  for i in range(5):
    chick2.layer.move(-10, -20)
    chick2.wing.rotate(-10)
  for i in range(5):
    chick2.layer.move(-10, 20)
    chick2.wing.rotate(10)
        
canvas.wait()
canvas.close()
