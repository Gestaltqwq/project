import math
def Decompose(i):#分解质数
    num_list = []
    while True:
        for j in range(2,int(i)+1):
            if i % j == 0 and i != j:
                i = i / j
                num_list.append(j)
                break
            if i == j:
                num_list.append(j)
                print(num_list)
                return

Decompose(int(input("输入需要分解的正整数:")))


