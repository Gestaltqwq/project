count = int(input("重复次数:"))
num = int(input("重复的数字:"))
temp_num = num
sum = num
for i in range(count-1):
    temp_num = temp_num * 10 + num
    sum += temp_num
print(sum)