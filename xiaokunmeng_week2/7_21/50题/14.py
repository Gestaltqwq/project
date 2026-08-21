time = input("请输入年月日(格式:年,月,日)：")
time_list = time.split(',')
match int(time_list[1]):
    case 1:
        count = 31
    case 2:
        count = 28 + 31
    case 3:
        count = 31 + 28 + 31
    case 4:
        count = 30 + 31 + 28 + 31
    case 5:
        count = 31 + 30 + 31 + 28 + 31
    case 6:
        count = 30 + 31 + 30 + 31 + 28 + 31
    case 7:
        count = 31 + 30 + 31 + 30 + 31 + 28 + 31
    case 8:
        count = 31 + 31 + 30 + 31 + 30 + 31 + 28 + 31
    case 9:
        count = 30 + 31 + 31 + 30 + 31 + 30 + 31 + 28 + 31
    case 10:
        count = 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31 + 28 + 31
    case 11:
        count = 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31 + 28 + 31
    case 12:
        count = 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31 + 28 + 31
if int(time_list[0]) % 4 == 0 and int(time_list[0]) % 100 != 0 or int(time_list[0]) % 400 == 0:
    count += 1
count = count - int(time_list[2])
print(f"{time}是{count}天")