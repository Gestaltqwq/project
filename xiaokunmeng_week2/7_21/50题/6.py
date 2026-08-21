def get_num(a,b):
    temp = 0
    max = 0
    count = a * b
    if a > b:
        temp = b
        b = a
        a = temp #a小b大
    while True:
        if a % b == 0:
            max = b
            break
        temp = a % b
        a = b
        b = temp
    count = count / max
    print("最大公约数是：",max)
    print("最小公倍数是：",int(count))

num_a = int(input("请输入第一个数字："))
num_b = int(input("请输入第二个数字："))
get_num(num_a,num_b)