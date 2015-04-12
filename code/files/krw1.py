#
# Read KRW-USD rates
#

# We have data from 1994 to 2009
years = range(1994, 2010)

# read one year into list data
def read_year(yr, data):
  fname = "data/%d.txt" % yr
  f = open(fname, "r")
  for l in f:
    date1, value1 = l.split()
    value = float(value1)
    # convert to KRW per USD
    value = int(1.0 / value)
    # convert YYYY/MM/DD string to int
    ys, ms, ds = date1.split("/")
    date = 10000 * int(ys) + 100 * int(ms) + int(ds)
    data.append((date, value))
  f.close()

# read all files and return list
def read_all():
  data = []
  for yr in years:
    read_year(yr, data)
  return data

# compute average exchange rate for yr
def average(data, yr):
  sum = 0
  count = 0
  start = yr * 10000 
  end = (yr + 1) * 10000
  for d, v in data:
    if start <= d < end:
      sum += v
      count += 1
  return sum / count

def find_min(data):
  vm = 99999
  dm = None
  for d, v in data:
    if v < vm:
      vm = v
      dm = d
  return dm, vm

def find_max(data):
  vm = 0
  dm = None
  for d, v in data:
    if v > vm:
      vm = v
      dm = d
  return dm, vm

def main():
  data = read_all()
  print "Minimum:", find_min(data)
  print "Maximum:", find_max(data)
  for yr in years:
    avg = average(data, yr)
    print yr, avg

main()
