#
# Blackjack Game, graphics version
#

import random
import time
import sys
from cs1graphics import *

FACES = range(2, 11) + ['Jack', 'Queen', 'King', 'Ace' ]
SUITS = [ 'Clubs', 'Diamonds', 'Hearts', 'Spades' ]
CARD_SIZE = (40, 80)
RADIUS = 3

# --------------------------------------------------------------------

class Card(object):
  """A card has a face and suit."""

  def __init__(self, face, suit):
    assert(face in FACES and suit in SUITS)
    self.face = face
    self.suit = suit
    self.graphics = None

  def __str__(self):
    return str(self.face) + " of " + self.suit

  def value(self):
    """Returns the face value of the card."""
    if type(self.face) == int:
      return self.face
    if self.face == "Ace":
      return 11
    return 10

# --------------------------------------------------------------------

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

# --------------------------------------------------------------------

def create_clubs(symbol):
  """Create clubs on layer symbol."""
  circle1 = Circle(RADIUS, Point(0, -RADIUS))
  circle1.setFillColor('black')
  circle1.setBorderWidth(0)
  symbol.add(circle1)
            
  circle2 = Circle(RADIUS, Point(-RADIUS, 0))
  circle2.setFillColor('black')
  circle2.setBorderWidth(0)
  symbol.add(circle2)
    
  circle3 = Circle(RADIUS, Point(RADIUS, 0))
  circle3.setFillColor('black')
  circle3.setBorderWidth(0)
  symbol.add(circle3)
  
  triangle = Polygon(Point(0, 0), 
                     Point(-RADIUS*2, RADIUS*3), 
                     Point(RADIUS*2, RADIUS*3))
  triangle.setFillColor('black')
  triangle.setBorderWidth(0)
  symbol.add(triangle)
  
def create_diamonds(symbol):            
  diamond = Square(3 * RADIUS)
  diamond.setFillColor('red')
  diamond.setBorderWidth(0)
  diamond.rotate(45)
  symbol.add(diamond)
        
def create_hearts(symbol):
  circle1 = Circle(RADIUS, Point(-RADIUS, -RADIUS))
  circle1.setFillColor('red')
  circle1.setBorderWidth(0)
  symbol.add(circle1)
            
  circle2 = Circle(RADIUS, Point(RADIUS, -RADIUS))
  circle2.setFillColor('red')
  circle2.setBorderWidth(0)
  symbol.add(circle2)
            
  triangle = Polygon(Point(-RADIUS*2, -RADIUS), 
                     Point(RADIUS*2, -RADIUS), 
                     Point(0, RADIUS*2))
  triangle.setFillColor('red')
  triangle.setBorderWidth(0)
  symbol.add(triangle)

def create_spades(symbol):        
  circle1 = Circle(RADIUS, Point(-RADIUS, RADIUS))
  circle1.setFillColor('black')
  circle1.setBorderWidth(0)
  symbol.add(circle1)
            
  circle2 = Circle(RADIUS, Point(RADIUS, RADIUS))
  circle2.setFillColor('black')
  circle2.setBorderWidth(0)
  symbol.add(circle2)
  
  triangle1 = Polygon(Point(-RADIUS*2, RADIUS), 
                      Point(RADIUS*2, RADIUS), 
                      Point(0, -RADIUS*2))
  triangle1.setFillColor('black')
  triangle1.setBorderWidth(0)
  symbol.add(triangle1)
  
  triangle2 = Polygon(Point(0, 0), 
                      Point(-RADIUS*2, RADIUS*4), 
                      Point(RADIUS*2, RADIUS*4))
  triangle2.setFillColor('black')
  triangle2.setBorderWidth(0)
  symbol.add(triangle2)

# --------------------------------------------------------------------

class CardGraphics(object):
  """Graphical representation of a card."""
  
  def __init__(self, card, hidden = False):
    self.l = Layer()

    self.hidden = hidden


    # background card
    self.bg = Rectangle(CARD_SIZE[0], CARD_SIZE[1])
    if hidden:
      self.bg.setDepth(0)
      self.bg.setFillColor('gray')
    else:
      self.bg.setDepth(100)
      self.bg.setFillColor('white')
    self.l.add(self.bg)
    
    # symbol for center
    symbol = Layer()
    if card.suit == "Diamonds":
      create_diamonds(symbol)
    elif card.suit == "Clubs":
      create_clubs(symbol)
    elif card.suit == "Hearts":
      create_hearts(symbol)
    else:
      create_spades(symbol)
    self.l.add(symbol)
    
    # text for left-top and right-bottom
    if card.suit in ['Diamonds', 'Hearts']:
      color = 'red'
    else:
      color = 'black'

    if type(card.face) == int:
      num = str(card.face)
    else:
      num = card.face[0]
    
    # left-top text
    lt_num = Text()
    lt_num.setMessage(num)
    lt_num.setFontColor(color)
    lt_num_dim = lt_num.getDimensions()
    lt_num.moveTo(-CARD_SIZE[0]/2 + lt_num_dim[0]/2, 
                   -CARD_SIZE[1]/2 + lt_num_dim[1]/2)
    self.l.add(lt_num)
        
    # right-bottom text
    rb_num = Text()
    rb_num.setMessage(num)
    rb_num.setFontColor(color)
    rb_num_dim = lt_num.getDimensions()
    rb_num.moveTo(CARD_SIZE[0]/2 - rb_num_dim[0]/2, 
                  CARD_SIZE[1]/2 - rb_num_dim[1]/2)
    self.l.add(rb_num)


  def show(self):
    self.bg.setDepth(100)
    self.bg.setFillColor('white')
    
# --------------------------------------------------------------------

class Hand(object):
  """A hand of cards displayed on a table."""

  def __init__(self, x, y, canvas):
    """Create an empty hand displayed at indicated position on canvas."""
    self.canvas = canvas
    self.x = x
    self.y = y
    self.graphics = []
    self.hand = []

  def clear(self):
    """Make hand empty."""
    for item in self.graphics:
      self.canvas.remove(item.l)
    self.graphics = []
    self.hand = []

  def add(self, card, hidden = False):
    """Add a new card to the hand."""
    self.hand.append(card)
    gr = CardGraphics(card, hidden)
    x0 = self.canvas.getWidth() + CARD_SIZE[0]/2
    x1 = self.x + CARD_SIZE[0] * 2 * len(self.graphics)
    gr.l.moveTo(x0, self.y)
    self.canvas.add(gr.l)
    self.graphics.append(gr)
    for t in range(11):
      t = t / 10.0
      gr.l.moveTo((1-t) * x0 + t * x1, self.y)

  def show(self):
    """Make all cards visible."""
    for gr in self.graphics:
      gr.show()

  def value(self):
    """Return value of the hand."""
    value = 0
    for card in self.hand:
      value += card.value()
    return value

# --------------------------------------------------------------------

class Table(object):
  """A graphical Blackjack table for playing Blackjack."""
  
  def __init__(self):
    self.canvas = Canvas(600, 400, 'dark green', 'Black Jack 101')
    self.player = Hand(CARD_SIZE[0], CARD_SIZE[1], self.canvas)
    self.dealer = Hand(CARD_SIZE[0], 3 * CARD_SIZE[1], self.canvas)

    self.score = [ Text(), Text() ]
    for i in range(2):
      self.score[i].setFontColor('white')
      self.score[i].setFontSize(20)
      self.score[i].moveTo(self.canvas.getWidth() - CARD_SIZE[0], CARD_SIZE[1])
      self.canvas.add(self.score[i])
    self.score[1].move(0, 2 * CARD_SIZE[1])

    self.message = Text()
    self.message.setFontColor('red')
    self.message.setFontSize(20)
    dim = self.message.getDimensions()
    self.message.moveTo(self.canvas.getWidth() / 2 - dim[0] / 2, 
                        self.canvas.getHeight() - 80)
    self.canvas.add(self.message)

    self.question = Text()
    self.question.setFontColor('white')
    self.question.setFontSize(20)
    dim = self.question.getDimensions()
    self.question.moveTo(self.canvas.getWidth() / 2 - dim[0] / 2, 
                        self.canvas.getHeight() - 40)
    self.canvas.add(self.question)

  def clear(self):
    """Clear everything on the table."""
    self.player.clear()
    self.dealer.clear()
    self.message.setMessage("")
    self.question.setMessage("")
    for i in range(2):
      self.score[i].setMessage("")

  def set_score(self, which, text):
    self.score[which].setMessage(text)
    
  def show_message(self, text):
    self.message.setMessage(text)

  def ask(self, prompt):
    self.question.setMessage(prompt)
    while True:
      e = self.canvas.wait()
      d = e.getDescription()
      if d == "canvas close":
        sys.exit(1)
      if d == "keyboard":
        key = e.getKey() 
        if key == 'y':
          self.question.setMessage("")
          return True
        if key == 'n':
          self.question.setMessage("")
          return False
  
  def close(self):
    """Close the table to end playing."""
    self.canvas.close()
    
# --------------------------------------------------------------------

def blackjack(table):
  """Play one round of Blackjack.
  Returns 1 if player wins, -1 if dealer wins, and 0 for a tie."""

  deck = Deck()
    
  # initial two cards
  table.player.add(deck.draw())
  table.dealer.add(deck.draw(), True) 
  table.player.add(deck.draw())
  table.dealer.add(deck.draw())
  table.set_score(0, str(table.player.value()))

  # player's turn to draw cards
  while table.player.value() < 21:
    if not table.ask("Would you like another card?"):
      break
    table.player.add(deck.draw())
    table.set_score(0, str(table.player.value()))
  
  # if the player's score is over 21, the player loses immediately.
  if table.player.value() > 21:
    table.show_message("You went over 21! You lost!")
    return -1

  # show hidden card
  table.dealer.show()
  table.set_score(1, str(table.dealer.value()))
  while table.dealer.value() < 17:
    table.dealer.add(deck.draw())
    table.set_score(1, str(table.dealer.value()))

  player_total = table.player.value()
  dealer_total = table.dealer.value()

  if dealer_total > 21:
    msg = "The dealer went over 21! You win!"
    result = 1
  elif player_total > dealer_total:
    msg = "You win!"
    result = 1
  elif player_total < dealer_total:
    msg = "You lost!"
    result = -1
  else:
    msg = "You have a tie!"
    result = 0

  table.show_message(msg)
  return result

# --------------------------------------------------------------------

def game_loop():
  table = Table()
  while True:
    blackjack(table)    
    if not table.ask("Another round?"):
      break    
    table.clear()
  table.close()

game_loop()

# --------------------------------------------------------------------
