from subjects.base_exam import BaseExam
class EnglishExam(BaseExam):
    def __init__(self, subject_name, max_score, student_name):
        super().__init__(subject_name, max_score, student_name)

    def get_grade(self):
        if self.get_score() >= 90:
            return "优秀"
        elif self.get_score() >= 75:
            return "良好"
        elif self.get_score() >= 60:
            return "及格"
        else:
            return "不及格"
        
    def print_report_card(self):
        score = self.get_score()
        print(f"学生:{self.student_name}")
        print(f"科目:{self.subject_name}")
        print(f"成绩:{score}")
        print("听力:XX")
        print("阅读:XX")
        print("写作:XX")
        print(f"等级:{self.get_grade()}")
        print(f"加权:{self.calc_weighted_score(0.7)}")

if __name__ == "__main__":
    test = EnglishExam("英语",100,"张三")
    test.input_score(90)
    print(test.get_grade())
    test.print_report_card()