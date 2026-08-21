#sunday，monday，tuesday，wednesday，thursday，friday，saturday
def check_weekday(strs):
    if strs == "m":
        print("Monday")
    elif strs == "t":
        strs = input("输入第二个字母:")
        if strs == "u":
            print("Tuesday")
        elif strs == "h":
            print("Thursday")
        else:
            print("输入错误！")
    elif strs == "w":
        print("Wednesday")
    elif strs == "f":
        print("Friday")
    elif strs == "s":
        strs = input("输入第二个字母:")
        if strs == "a":
            print("Saturday")
        elif strs == "u":
            print("Sunday")
        else:
            print("输入错误！")
    else:
        print("输入错误！")

check_weekday(input("请输入星期的首字母:"))