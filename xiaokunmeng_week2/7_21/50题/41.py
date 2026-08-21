count = 0
while True:
    count += 1
    temp = count
    for i in range(5):
        if temp % 5 != 1:
            flag = False
            break
        else:
            temp = (temp-1) / 5 * 4
            flag = True
    if flag: break
print(count)