#
# Boy and Girl objects
#

class Boy(object):
  def __init__(self, s):
    self.description = s

  def jump(self):
    print self.description + " boy jumps"
  
  def sing(self):
    print self.description + " boy sings"

class Girl(object):
  def __init__(self, s):
    self.description = s

  def dance(self):
    print self.description + " girl dances"
  
  def sing(self):
    print self.description + " girl sings"

