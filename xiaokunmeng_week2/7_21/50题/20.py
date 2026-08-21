from fractions import Fraction
n = 1
m = 2
temp = 0
sum = 0
for i in range(0,20):
    sum += Fraction(n,m)
    temp = n + m
    n = m
    m = temp
print(round(sum,2))