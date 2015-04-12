
f = open("data/words.txt", "r")

count = 0
for line in f:
  word = line.strip()
  if not "e" in word:
    count += 1

print "%d words have no 'e'" % count
f.close()
