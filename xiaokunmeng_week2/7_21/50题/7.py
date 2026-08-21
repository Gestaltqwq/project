str = input("输入字符串：")
letter = num = space = other = 0
for i in str:
    if i.isalpha():
        letter += 1
    elif i.isdigit():
        num += 1
    elif i.isspace():
        space += 1
    else:
        other += 1
print(f"字母个数：{letter},数字个数：{num},空格个数：{space},其他字符个数：{other}")