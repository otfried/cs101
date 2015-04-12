
import random

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

class Deck(object):
  """A deck of cards."""
  def __init__(self):
    """Create a deck of 52 cards and shuffle them."""
    self.cards = []
    for suit in SUITS:
      for face in FACES:
        self.cards.append(Card(face, suit))
    random.shuffle(self.cards)

  def draw(self):
    """Draw the top card from the deck."""
    return self.cards.pop()

num_players = 3
num_cards = 5

deck = Deck()
hands = []

for j in range(num_players):
  hands.append([])

for i in range(num_cards):
  for j in range(num_players):
    card = deck.draw() 
    hands[j].append(card)
    print "Player", j+1, "draws", card

for j in range(num_players):
  print "Player %d's hand (value %d):" % (j+1, hand_value(hands[j]))
  for card in hands[j]:
    print " ", card

