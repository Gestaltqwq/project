import math
def Decompose(i):#提取真因子
    num_list = []
    while True:
        for j in range(1,int(i/2)+1):
            if i % j == 0:
                num_list.append(j)
        return num_list

for i in range(2,1000):
    num_list = Decompose(i)
    sum = 0
    for j in num_list:
        j = int(j)
        sum += j
    if i == sum:
        print(f"{i}是完数")