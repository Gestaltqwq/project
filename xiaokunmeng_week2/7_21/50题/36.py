def move_num(a,long):
    num_length = len(str(a))
    num_low = a % (10 ** long)
    num_high = a // (10 ** long)
    new_num = num_low * (10 ** (num_length - long)) + num_high
    return new_num

print(move_num(123456,2))