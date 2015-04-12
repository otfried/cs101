
def to_radix(n, b):
  if n < b:
    return str(n)
  s = to_radix(n / b, b)
  return s + str(n % b)

print to_radix(83790, 8)
print to_radix(83790, 2)
      
