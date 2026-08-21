for i in range(1,101):
    flag = 1
    for j in range(2,(round(i/2)+1)):
        if i % j == 0:
            flag = 0
            break
        else:
            continue
    if flag == 0:
        print(f"{i}是素数")
    else:
        continue
