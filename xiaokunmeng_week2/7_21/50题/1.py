def rabbit_count():
    a = 1
    b = 1
    temp = 0
    print(a) 
    print(b)
    for i in range(1,30):#斐波那契
        temp = a + b
        a = b
        b = temp
        print(temp)

rabbit_count()