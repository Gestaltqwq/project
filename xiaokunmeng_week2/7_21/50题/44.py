import math


def is_prime(num):
    for i in range(2,int(math.sqrt(num))+1):
        if num % i == 0:
            return False
    return True


def department(num):
    if num % 2 == 1:
        print("要输入偶数！")
        raise ValueError
    else:
        for i in range(2,int(num/2)+1):
            if is_prime(i) and is_prime(num-i):
                print(f"{num} = {i} + {num-i}")
                print(f"{num}可以分解为两个素数{i},{num-i}")
                break

department(int(input("请输入一个偶数：")))