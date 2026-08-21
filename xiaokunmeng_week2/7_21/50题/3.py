import math
def Narcissistic_number():
    for i in range(100,1000):
        a = i // 100
        b = i // 10 % 10
        c = i % 10
        count = math.pow(a,3) + math.pow(b,3) + math.pow(c,3)
        if count == i:
            print(f"{i}是水仙花数")

Narcissistic_number()