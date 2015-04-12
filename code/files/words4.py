
def three_doubles(word):
  s = ""
  for i in range(1,len(word)):
    if word[i-1] == word[i]:
      s = s + "*"
    else:
      s = s + " "
  return "* * *" in s

f = open("data/words.txt", "r")

for line in f:
  word = line.strip()
  if three_doubles(word):
    print word

f.close()
