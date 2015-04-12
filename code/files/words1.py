
f = open("data/words.txt", "r")

for line in f:
  word = line.strip()
  if len(word) > 18:
    print word

f.close()
