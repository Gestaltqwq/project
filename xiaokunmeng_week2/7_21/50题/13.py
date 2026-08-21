import math
for a in range(1,100000):
    b = a + 100
    if math.sqrt(b) % 1 == 0:
        b = b + 168
        if math.sqrt(b) % 1 == 0:
            print(a)
            break

 