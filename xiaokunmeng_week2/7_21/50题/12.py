def money(i):
    if i <= 100000:
        return i * 0.1
    elif i <= 200000:
        return (i - 100000) * 0.075 + money(100000)
    elif i <= 400000:
        return (i - 200000) * 0.05 + money(200000)
    elif i <= 600000:
        return (i - 400000) * 0.03 + money(400000)
    elif i <= 10000000:
        return (i - 600000) * 0.015 + money(600000)
    else:
        return (i - 10000000) * 0.01 + money(10000000)

print(money(int(input("请输入利润额："))))