from cs1graphics import *

canvas = Canvas(600, 200)
canvas.setBackgroundColor("light blue")

car = Layer()
tire1 = Circle(10, Point(-20,-10))
tire1.setFillColor('black')
car.add(tire1)
tire2 = Circle(10, Point(20,-10))
tire2.setFillColor('black')
car.add(tire2)
body = Rectangle(70, 30, Point(0, -25))
body.setFillColor('blue')
body.setDepth(60)
car.add(body)

car.moveTo(50, 150)
canvas.add(car)

canvas.wait()

for i in range(50):
  car.move(2, 0)
for i in range(22):
  car.rotate(-1)
for i in range(50):
  car.move(2,-1)
for i in range(22):
  car.rotate(1)
for i in range(50):
  car.move(2,0)
for i in range(10):
  car.scale(1.05)
car.flip(90)

canvas.wait()

canvas.close()
