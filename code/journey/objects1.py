class Card(object):
  """A Blackjack card."""
  pass

def card_string(card):
  article = "a "
  if card.face in [8, "Ace"]: article = "an "
  return article + str(card.face) + " of " + card.suit

def hand_value(hand):
  total = 0
  for card in hand:
    total += card.value
  return total

card = Card()
card.face = "Ace"
card.suit = "Spades"
card.value = 11

hand = [ card ]

print card_string(card), "has value", card.value
print "Hand has value", hand_value(hand)
