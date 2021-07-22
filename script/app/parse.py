import sys 

data = sys.argv[1]
data = data.split(',')

obj = dict() 
for d in data:
    arr = d.split(':')
    key = arr[0]
    val = arr[1]
    obj[key] = val 

print('PARSED DATA: ', obj)