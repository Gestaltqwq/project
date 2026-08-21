from fractions import Fraction
def get_sum(a):
    sum = 0
    if a % 2 == 0:
        for i in range(1,int(a/2+1)):
            sum += Fraction(1,2*i)
    elif a % 2 == 1:
        for i in range(1,int((a+1)/2+1)):
            sum += Fraction(1,2*i-1)
    return sum

print(get_sum(4))
print(get_sum(5))