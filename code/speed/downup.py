
def downup(w):
  print w
  if len(w) <= 1:
    return
  downup(w[:-1])
  print w

downup("CS101 is wonderful")

