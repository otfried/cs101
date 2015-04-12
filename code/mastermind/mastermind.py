#
# Mastermind Game
#

import random

max_num_guesses = 10

def create_secret():
  """Create secret: four distinct letters from A-F."""
  c = [ "A", "B", "C", "D", "E", "F" ]
  secret = ""
  for i in range(4):
    letter = random.choice(c)
    c.remove(letter)
    secret = secret + letter
  return secret

def check_guess(guess):
  """Check if guess is legal: Four distinct letters from A-F.
  Returns error message or None if guess is okay."""
  if len(guess) != 4:
    return "Your guess must have four letters"
  for i in range(4):
    letter = guess[i]
    if not letter in "ABCDEF":
      return "You can only use letters A, B, C, D, E, and F."
    for j in range(i):
      if letter == guess[j]:
        return "All letters must be distinct."
  # everything is fine!
  return None

def get_guess():
  while True:
    guess = raw_input("Enter your guess> ")
    guess = guess.strip().upper().replace(" ", "")
    err = check_guess(guess)
    if not err:
      return guess
    print err

def evaluate_guess(secret, guess):
  """Return (pos, let) where pos is the number of correct letters in the 
  correct position, and let is the number of correct letters in the 
  wrong position."""
  pos = 0
  let = 0
  for i in range(4):
    if guess[i] == secret[i]:
      pos += 1
    elif guess[i] in secret:
      let += 1
  return pos, let
  
def show_history(h, secret):
  count = 0
  for guess in h:
    pos, let = evaluate_guess(secret, guess)
    count += 1
    print "%2d: %s : %d positions, %d letters" % (count, guess, pos, let)
  
def main():    
  secret = create_secret()
  history = []
  print "Welcome to Mastermind!"
  print "I have created a secret combination:",
  print "Four distinct letters from A - F."
  print "You have %d guesses to find it." % max_num_guesses
  while True:
    show_history(history, secret)
    if len(history) == max_num_guesses:
      print ("My secret was %s, you failed to find it in %d guesses!" %
             (secret, len(history)))
      return
    guess = get_guess()
    history.append(guess)
    pos, let = evaluate_guess(secret, guess)
    if pos == 4:
      print ("My secret was %s, you guessed correctly in %d guesses!" % 
             (secret, len(history)))
      return

main()
