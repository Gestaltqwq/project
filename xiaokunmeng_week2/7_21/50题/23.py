def how_old(a,count):
    if count == 5:
        return a
    return how_old(a + 2,count + 1)

print(how_old(10,1))