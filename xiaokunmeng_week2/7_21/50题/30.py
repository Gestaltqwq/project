def append_num(a,num_list):
    flag = 1
    if num_list[0] > num_list[-1]:
        flag = 0
    if flag == 1 and a < num_list[0]:
        num_list.insert(0,a)
    elif flag == 1 and a > num_list[-1]:
        num_list.append(a)
    elif flag == 0 and a > num_list[0]:
        num_list.insert(0,a)
    elif flag == 0 and a < num_list[-1]:
        num_list.append(a)
    elif flag == 1 :
        for i in range(1,len(num_list)-1):
            if a > num_list[i] and a < num_list[i+1]:
                num_list.insert(i+1,a)
                break
    elif flag == 0 :
        for i in range(1,len(num_list)-1):
            if a < num_list[i] and a > num_list[i+1]:
                num_list.insert(i+1,a)
                break
    return num_list


num_list = [1,2,6,7,8,9,10]
a = int(input("请输入一个数字："))
num_list = append_num(a,num_list)
print(num_list)
