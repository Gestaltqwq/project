def how_long(a):
    num_list = []
    if a // 10000 == 0:
        if a// 1000 == 0:
            if a // 100 == 0:
                if a // 10 == 0:
                    num_list.append(a)
                    return 1, num_list
                num_list.append(a % 10)
                num_list.append(a // 10)
                return 2, num_list
            num_list.append(a % 10)
            num_list.append(a % 100 // 10)
            num_list.append(a // 100)
            return 3, num_list
        num_list.append(a % 10)
        num_list.append(a % 100 // 10)
        num_list.append(a % 1000 // 100)
        num_list.append(a // 1000)
        return 4, num_list
    num_list.append(a % 10)
    num_list.append(a % 100 // 10)
    num_list.append(a % 1000 // 100)
    num_list.append(a % 10000 // 1000)
    num_list.append(a // 10000)
    return 5, num_list

long,num_list = how_long(int(input("请输入一个数字(不超过5位数)：")))
print(f"这个数字有{long}位")
for i in num_list:
    print(i,end=" ")
