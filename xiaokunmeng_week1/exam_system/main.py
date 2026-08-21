from subjects import BaseExam, ChineseExam, MathExam, EnglishExam
from grade_utils import (
    calc_percentage,
    save_record,
    read_all_records,
    get_excellent_students,
    report_card_generator,
    multi_thread_input_test,
    check_balance,
)


def main():
    print("基础得分率计算测试")
    pct = calc_percentage(90, 150)
    print(f"得分率：90/150 = {pct:.1f}%")
    print()

    print("成绩保存与读取测试")
    save_record("张三,语文,95,良好")
    save_record("张三,英语,90,优秀")
    save_record("张三,数学,130,优秀")
    records = read_all_records()
    for r in records:
        print(f"读取到：{r}")
    print()

    print("多线程录入测试")
    multi_thread_input_test()
    print()

    print("设置及格率为 0.65")
    BaseExam.set_passing_rate(0.65)
    print(f"当前及格率：{BaseExam.passing_rate}")
    print()

    print("语文测试")
    chinese = ChineseExam("语文", 150, "小明")
    try:
        chinese.input_score("tert")
    except ValueError as e:
        print(e)
    except TypeError:
        print("参数类型错误")
    chinese.input_essay_score(50)
    print(f"姓名：{chinese.student_name}")
    print(f"成绩：{chinese.get_score()}")
    print(f"作文分：{chinese.show_essay_score()}")
    print(f"等级：{chinese.get_grade()}")
    save_record(f"{chinese.student_name},{chinese.subject_name},{chinese.get_score()},{chinese.get_grade()}")
    print()

    print("数学测试")
    math = MathExam("数学", 150, "李四")
    try:
        math.input_score(130)
    except ValueError as e:
        print(e)
    except TypeError as e:
        print("参数类型错误")
    math.set_bonus_points(20)
    print(f"姓名：{math.student_name}")
    print(f"成绩：{math.get_score()}")
    print(f"附加分：{math.get_bonus_points()}")
    print(f"加权分(0.7)：{math.calc_weighted_score(0.7)}")
    print(f"等级：{math.get_grade()}")
    save_record(f"{math.student_name},{math.subject_name},{math.get_score()},{math.get_grade()}")
    print()

    print("英语测试")
    english = EnglishExam("英语", 100, "王五")
    try:
        english.input_score(88)
    except ValueError as e:
        print(e)
    except TypeError as e:
        print("参数类型错误")
    print(f"等级：{english.get_grade()}")
    english.print_report_card()
    save_record(f"{english.student_name},{english.subject_name},{english.get_score()},{english.get_grade()}")
    print()

    print("优秀学生筛选测试")
    score_dict = {
        "张三": 128,
        "李四": 145,
        "王五": 88,
        "赵六": 136,
    }
    excellent = get_excellent_students(score_dict, 135)
    print(f"成绩字典：{score_dict}")
    print(f"优秀线设置为：135")
    print(f"优秀学生：{excellent}")
    print()

    print("成绩单生成器测试")
    c2 = ChineseExam("语文", 150, "赵六")
    c2.input_score(136)
    m2 = MathExam("数学", 150, "李四")
    m2.input_score(130)
    e2 = EnglishExam("英语", 100, "王五")
    e2.input_score(88)
    print("成绩单：")
    for card in report_card_generator([c2, m2, e2]):
        print(f"{card}")
    print()

    print("批量统计多态测试")
    chi = ChineseExam("语文", 150, "张三")
    chi.input_score(128)
    mat = MathExam("数学", 150, "李四")
    mat.input_score(130)
    mat.set_bonus_points(10)
    eng = EnglishExam("英语", 100, "王五")
    eng.input_score(92)
    exams = [chi, mat, eng]
    for exam in exams:
        w = exam.calc_weighted_score(0.7)
        print(f"{exam.student_name} {exam.subject_name}：原始分 {exam.get_score()}，加权分(0.7) = {w}")
    print()

    print("偏科测试")
    score = {}
    records = read_all_records()
    name = "张三"
    for i in records:
        strs = i.split(",")
        if strs[0] == name:
            score[strs[1]] = int(strs[2])
    check_balance(score)


if __name__ == "__main__":
    main()
