
f = open("data/planets.txt", "r")
earth = 0
for line in f:
  earth += 1
  planet = line.strip().lower()
  if planet == "earth":
    break

print "Earth is planet #%d" % earth
