def input_data(count):
    for _ in range(count):
        id = int(input("请输入学生id:"))
        name = input("请输入学生姓名:")
        math_score = float(input("请输入学生数学成绩:"))
        if math_score < 0 or math_score > 150:
            raise ValueError("输入的分数有误")
        chinese_score = float(input("请输入学生语文成绩:"))
        if chinese_score < 0 or chinese_score > 150:
            raise ValueError("输入的分数有误")
        english_score = float(input("请输入学生英语成绩:"))
        if english_score < 0 or english_score > 150:
            raise ValueError("输入的分数有误")
        average_score = round((math_score + chinese_score + english_score) / 3,2)
        with open("stud.txt", "a", encoding="utf-8") as f:
            f.write(f"id:{id},姓名:{name},数学成绩:{math_score},语文成绩:{chinese_score},英语成绩:{english_score},平均成绩:{average_score}\n")
def show_data():
    with open("stud.txt", "r", encoding="utf-8") as f:
        for line in f:
            print(line.strip())
show_data()
#input_data(5)