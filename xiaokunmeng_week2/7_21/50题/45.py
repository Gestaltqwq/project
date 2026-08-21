import math

def how_many_nine(num):
    count = 0
    while True:
        if num % 9 == 0:
            count += 1
        else:
            return count

def is_prime(num):
    for i in range(2,int(math.sqrt(num))+1):
        if num % i == 0:
            return False
    return True


num = int(input("请输入一个素数："))
if is_prime(num):
    print(how_many_nine(num))
else:
    print("输入的不是素数")