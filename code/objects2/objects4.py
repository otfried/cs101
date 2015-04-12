FACES = range(2, 11) + ['Jack', 'Queen', 'King', 'Ace' ]
SUITS = [ 'Clubs', 'Diamonds', 'Hearts', 'Spades' ]

class Card(object):
  """A Blackjack card."""

  def __init__(self, face, suit):
    assert face in FACES and suit in SUITS
    self.face = face
    self.suit = suit

  def __str__(self):
    article = "a "
    if self.face in [8, "Ace"]: article = "an "
    return article + str(self.face) + " of " + self.suit

  def value(self):
    if type(self.face) == int:
      return self.face
    elif self.face == "Ace":
      return 11
    else:
      return 10

def hand_value(hand):
  total = 0
  for card in hand:
    total += card.value()
  return total

hand = [ Card("Ace", "Spades"),
         Card(8, "Diamonds"),
         Card("Jack", "Hearts"),
         Card(10, "Clubs") ]

for card in hand:
  print card, "has value", card.value()

print "Hand has value", hand_value(hand)
