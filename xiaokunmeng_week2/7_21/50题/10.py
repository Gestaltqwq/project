high = 100
long = high
for i in range(1,10):
    high = high / 2
    long = long + 2*high
print(round(long,2))
print(round(high/2,2))