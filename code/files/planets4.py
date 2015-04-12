
f = open("data/planetsc.txt", "r")
earth = 0
for line in f:
  planet = line.strip().lower()
  if planet[0] == "#":
    continue
  earth += 1
  if planet == "earth":
    break

print "Earth is planet #%d" % earth
