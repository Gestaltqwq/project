def num_trans(num):
    num = list(str(num))
    if len(num) != 4:
        raise ValueError("输入的数字长度必须为4位")
    else:
        for i in range(len(num)):
            num[i] = (int(num[i]) + 5) % 10
        num[0],num[-1]=num[-1],num[0]
        num[1],num[-2]=num[-2],num[1]
        new_num = ''
        for j in num:
            new_num += str(j)
        return int(new_num)
    
print(num_trans(5678))
