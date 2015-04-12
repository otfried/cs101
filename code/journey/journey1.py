#
# Journey of Chicken I
#
# Jeong-eun Yu and Geum-hyeon Song
#

from cs1graphics import*

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

chicken = Layer()
chick1 = Layer()
chick2 = Layer()
herd = Layer()

# mother hen
body = Ellipse(70,80)
body.setFillColor("white")
body.setBorderColor("yellow")
body.move(600,200)
body.setDepth(20)
chicken.add(body)

wing = Ellipse(60,40)
wing.setFillColor("white")
wing.setBorderColor("yellow")
wing.move(615,220)
wing.setDepth(19)
chicken.add(wing)

eye = Circle(3)
eye.setFillColor("black")
eye.move(585,185)
eye.setDepth(18)
chicken.add(eye)

beak = Square(8)
beak.rotate(45)
beak.setFillColor("orange")
beak.setBorderColor("orange")
beak.setDepth(21)
beak.move(564,200)
chicken.add(beak)

head1 = Ellipse(5, 8)
head1.setFillColor("red")
head1.setBorderColor("red")
head1.move(600, 158)
head1.setDepth(22)
chicken.add(head1)

head2 = Ellipse(5, 8)
head2.setFillColor("red")
head2.setBorderColor("red")
head2.move(594, 158)
head2.setDepth(22)
chicken.add(head2)

# first chicken
body1 = Ellipse(40,50)
body1.setFillColor("yellow")
body1.setBorderColor("yellow")
body1.move(720,210)
body1.setDepth(20)
chick1.add(body1)

wing1 = Ellipse(30,20)
wing1.setFillColor("yellow")
wing1.setBorderColor("orange")
wing1.move(730,225)
wing1.setDepth(19)
chick1.add(wing1)

eye1 = Circle(2)
eye1.setFillColor("black")
eye1.move(710,200)
eye1.setDepth(18)
chick1.add(eye1)

beak1 = Square(4)
beak1.rotate(45)
beak1.setFillColor("orange")
beak1.setBorderColor("orange")
beak1.setDepth(21)
beak1.move(698,210)
chick1.add(beak1)

# second chicken
body2 = Ellipse(40,50)
body2.setFillColor("yellow")
body2.setBorderColor("yellow")
body2.move(800,210)
body2.setDepth(20)
chick2.add(body2)

wing2 = Ellipse(30,20)
wing2.setFillColor("yellow")
wing2.setBorderColor("orange")
wing2.move(810,225)
wing2.setDepth(19)
chick2.add(wing2)

eye2 = Circle(2)
eye2.setFillColor("black")
eye2.move(790,200)
eye2.setDepth(18)
chick2.add(eye2)

beak2 = Square(4)
beak2.rotate(45)
beak2.setFillColor("orange")
beak2.setBorderColor("orange")
beak2.setDepth(21)
beak2.move(778,210)
chick2.add(beak2)

herd.add(chicken)
herd.add(chick1)

canvas.add(herd)
canvas.add(chick2)

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
  wing2.adjustReference(-5, -5)
  for i in range(5):
    chick2.move(-10, -20)
    wing2. rotate(-10)
  for i in range(5):
    chick2.move(-10, 20)
    wing2.rotate(10)
        
canvas.wait()
canvas.close()
