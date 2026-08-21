def muti(a):
    if a == 1:
        return 1
    return a * muti(a-1)

print(muti(5))