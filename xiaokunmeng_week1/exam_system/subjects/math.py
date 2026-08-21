from subjects.base_exam import BaseExam
class MathExam(BaseExam):
    def __init__(self, subject_name, max_score, student_name):
        super().__init__(subject_name, max_score, student_name)
        self.__bonus_points = 0
    
    def get_bonus_points(self):
        return self.__bonus_points
    
    def set_bonus_points(self, bonus_points):
        self.__bonus_points = bonus_points

    def get_grade(self):
        if self.get_score() >= 140:
            return "优秀"
        elif self.get_score() >= 120:
            return "良好"
        elif self.get_score() >= 90:
            return "及格"
        else:
            return "不及格"
        
    def calc_weighted_score(self, weight):
        return (self.get_score() + self.__bonus_points)* weight
    
if __name__ == "__main__":
    test = MathExam("数学",150,"张三")
    test.input_score(120)
    test.set_bonus_points(20)
    print(test.get_grade())
    test.print_report_card()