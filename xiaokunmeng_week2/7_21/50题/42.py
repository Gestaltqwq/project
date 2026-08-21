num = 10
while True:
    if num*809 != 800*num + 9*num+1:
        num += 1
        continue
    else:
        if len(str(8*num)) != 2:
            num += 1
            continue
        elif len(str(9*num)) != 3:
            num += 1
            continue
        else:
            print(num)
            print(809*num)
            break