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

  def __eq__(self, rhs):
    return (self.face == rhs.face and 
            self.suit == rhs.suit)

  def __ne__(self, rhs):
    return not self == rhs

  def value(self):
    if type(self.face) == int:
      return self.face
    elif self.face == "Ace":
      return 11
    else:
      return 10

