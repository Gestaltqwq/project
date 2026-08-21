import math
def prime_number():
    count = 0
    for i in range(101,200):
        for j in range(2,int(math.sqrt(i))+1):
            if i % j == 0:
                break
        else:
            count += 1
            print(f"{i}是素数")
    print(f"素数个数为{count}")

prime_number()