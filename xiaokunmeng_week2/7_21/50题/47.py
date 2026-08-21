def print_sign(num_list):
    for i in num_list:
        for j in range(i):
            print("*",end="")
        print()

num_list = []
for i in range(7):
    num_list.append(int(input("请输入数字：")))
print_sign(num_list)