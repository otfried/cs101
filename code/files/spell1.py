
word_file = "../files/data/words.txt"

def read_words():
  words = []
  f = open(word_file, "r")
  for line in f:
    words.append(line.strip())
  f.close()
  return words

def main():
  words = read_words()
  while True:
    w = raw_input("Enter a word> ")
    w = w.strip()
    if w == "":
      break
    if w in words:
      print "%s is a word" % w
    else:
      print "Spelling error: %s is not a word!" % w

main()
