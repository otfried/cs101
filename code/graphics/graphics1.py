from cs1graphics import *

canvas = Canvas(400, 300)
canvas.setBackgroundColor("light blue")
canvas.setTitle("CS101 Drawing exercise")

sq = Square(100)
sq.setFillColor("blue")
sq.setBorderColor("red")
sq.setBorderWidth(5)
sq.moveTo(200, 200)
canvas.add(sq)

canvas.wait()

r = Rectangle(150, 75)
r.setFillColor("yellow")
r.moveTo(280, 150)
canvas.add(r)

canvas.wait()

sq.setDepth(10)
r.setDepth(20)

canvas.wait()

sq.rotate(45)

canvas.wait()

sq.scale(1.5)
r.scale(0.5)

canvas.wait()

for i in range(80):
  sq.scale(0.95)
canvas.remove(sq)

canvas.wait()
canvas.close()
