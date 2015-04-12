
import random

def merge(a, a1, a2):
  i1 = 0
  i2 = 0
  i = 0
  while i1 < len(a1) and i2 < len(a2):
    if a1[i1] < a2[i2]:
      a[i] = a1[i1]
      i1 += 1
    else:
      a[i] = a2[i2]
      i2 += 1
    i += 1
  while i1 < len(a1):
    a[i] = a1[i1]
    i1 += 1
    i += 1
  while i2 < len(a2):
    a[i] = a2[i2]
    i2 += 1
    i += 1
  
def sort(a):
  if len(a) <= 1:
    return
  m = len(a)/2
  a1 = a[:m]
  a2 = a[m:]
  sort(a1)
  sort(a2)
  merge(a, a1, a2)
  
a = range(1, 2001)
random.shuffle(a)
print a[:100]
sort(a)
print a[:100]
