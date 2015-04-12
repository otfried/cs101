
def is_abecedarian(word):
  for i in range(1,len(word)):
    if word[i-1] > word[i]:
      return False
  return True

f = open("data/words.txt", "r")

count = 0
for line in f:
  word = line.strip()
  if is_abecedarian(word):
    print word
    count += 1

print "%d words are abecedarian" % count
f.close()
