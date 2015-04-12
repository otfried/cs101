
def card_string(card):
  article = "a "
  if card[0] in [8, "Ace"]: article = "an "
  return article + str(card[0]) + " of " + card[1]

def hand_value(hand):
  total = 0
  for card in hand:
    total += card[2]
  return total

card = ("Ace", "Spades", 11)

hand = [ card ]

print card_string(card), "has value", card[2]
print "Hand has value", hand_value(hand)
