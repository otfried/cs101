
countries = [ "Australia", "Austria", "Belarus", "Canada",
              "China", "Croatia", "Czech Republic", "Estonia",
              "Finland", "France", "Germany", "Great Britain",
              "Italy", "Japan", "Kazakhstan", "Korea", "Latvia",
              "Netherlands", "Norway", "Poland", "Russian Federation",
              "Slovakia", "Slovenia", "Sweden", "Switzerland",
              "United States" ]

gold = [2, 4, 1, 14, 5, 0, 2, 0, 0, 2, 10, 1, 1, 
        0, 0, 6, 0, 4, 9, 1, 3, 1, 0, 5, 6, 9]

silver = [1, 6, 1, 7, 2, 2, 0, 1, 1, 3, 13, 0, 1, 3, 1, 
          6, 2, 1, 8, 3, 5, 1, 2, 2, 0, 15]

bronze = [0, 6, 1, 5, 4, 1, 4, 0, 4, 6, 7, 0, 3, 2, 0, 
          2, 0, 3, 6, 2, 7, 1, 1, 4, 3, 13]

def no_medals(countries, al, bl):
  result = []
  for i in range(len(countries)):
    if al[i] == 0 and bl[i] == 0:
      result.append(countries[i])
  return result

only_gold = no_medals(countries, silver, bronze)
only_silver = no_medals(countries, gold, bronze)
only_bronze = no_medals(countries, gold, silver)

only_one = only_gold + only_silver + only_bronze

print only_one

