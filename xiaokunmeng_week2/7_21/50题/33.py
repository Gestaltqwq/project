up_floor = []
down_floor = []
up_floor.append(1)
for i in range(1,11):
    print(f"{" "*(10-i)}",end="")
    for k in up_floor:
        print(k,end=" ")
    print(f"{" "*(9-i)}",end="")
    print()
    for j in range(i+1):
        if j == 0 or j == i:
            down_floor.append(1)
        else:
            down_floor.append(up_floor[j-1]+up_floor[j])
    up_floor = down_floor
    down_floor = []