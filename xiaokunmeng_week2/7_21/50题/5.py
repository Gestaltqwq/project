score = int(input("输入分数:"))
level = "A" if score >= 90 else ("B" if score >= 80 else "C")
print(level)