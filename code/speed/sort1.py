
import random

def sort(a):
  for i in range(len(a) - 1):
    for j in range(len(a) - 1):
      if a[j] > a[j+1]:
        a[j], a[j+1] = a[j+1], a[j]
  
a = range(1, 2001)
random.shuffle(a)
print a[:100]
sort(a)
print a[:100]
