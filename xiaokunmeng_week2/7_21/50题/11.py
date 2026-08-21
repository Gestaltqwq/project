for i in range(1,5):#百位数
    str1 = ''
    str1 += str(i)
    temp_str_1 = str1 #存储百位数
    for j in range(1,5):
        str1 = temp_str_1 #重置只有百位数
        if str(j) not in str1:
            str1 += str(j)
            temp_str_2 = str1 #存储百位和十位
        else:
            continue
        for k in range(1,5):
            if str(k) not in str1:
                str1 += str(k)
                if len(str1) == 3:
                    print(str1)
                    str1 = temp_str_2 #重置只有百位和十位
                    continue
