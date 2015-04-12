medals = [ ( 'Australia', 2, 1, 0 ),
           ( 'Austria', 4, 6, 6 ),
           ( 'Belarus', 1, 1, 1 ),
           ( 'Canada', 14, 7, 5 ),
           ( 'China', 5, 2, 4 ),
           ( 'Croatia', 0, 2, 1 ),
           ( 'Czech Republic', 2, 0, 4 ),
           ( 'Estonia', 0, 1, 0 ),
           ( 'Finland', 0, 1, 4 ),
           ( 'France', 2, 3, 6 ),
           ( 'Germany', 10, 13, 7 ),
           ( 'Great Britain', 1, 0, 0 ),
           ( 'Italy', 1, 1, 3 ),
           ( 'Japan', 0, 3, 2 ),
           ( 'Kazakhstan', 0, 1, 0 ),
           ( 'Korea', 6, 6, 2 ),
           ( 'Latvia', 0, 2, 0 ),
           ( 'Netherlands', 4, 1, 3 ),
           ( 'Norway', 9, 8, 6 ),
           ( 'Poland', 1, 3, 2 ),
           ( 'Russian Federation', 3, 5, 7 ),
           ( 'Slovakia', 1, 1, 1 ),
           ( 'Slovenia', 0, 2, 1 ),
           ( 'Sweden', 5, 2, 4 ),
           ( 'Switzerland', 6, 0, 3 ),
           ( 'United States', 9, 15, 13 ) ]

def print_totals():
  for country, g, s, b in medals:
    print country + ":", g + s + b

def print_totals2():
  for item in medals:
    print item[0] + ":", sum(item[1:])

def compare(item1, item2):
  medals1 = sum(item1[1:])
  medals2 = sum(item2[1:])
  return -cmp(medals1, medals2)

def top_ten():
  medals.sort(compare)
  top_ten = medals[:10]
  for item in top_ten:
    print item[0] + ":", sum(item[1:])

def histogram():
  t = [0] * 13
  for item in medals:
    total = sum(item[1:])
    t[total / 3] += 1
  for i in range(13):
    print str(3*i) + "~" + str(3*i+2) + ":\t" + ("*" * t[i])

histogram()
