def get_num(num:int):
    num = num // 1000
    num = num % 10000
    return num

num = get_num(123456789)
print(num)
