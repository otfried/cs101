
planets = []

f = open("data/planets.txt", "r")
for line in f:
  planets.append(line.strip())
f.close()  

print planets
