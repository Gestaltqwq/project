def str_sort(str1):
    for i in range(len(str1)):
        for j in range(i+1,len(str1)):
            if str1[i] > str1[j]:
                str1[i],str1[j] = str1[j],str1[i]
    return str1

str_list = list(input("请输入一个字符串："))
print(str_sort(str_list))