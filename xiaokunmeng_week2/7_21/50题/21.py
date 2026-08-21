def mutil(a):
    sum = 1
    for i in range(1,a+1):
        sum = sum * i
    return sum

sum = 0
for i in range(1,21):
    sum += mutil(i)
print(sum)