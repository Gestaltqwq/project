from subjects.base_exam import BaseExam
class ChineseExam(BaseExam):
    def __init__(self,subject_name:str,max_score:float,student_name:str):
        super().__init__(subject_name,max_score,student_name)
        self.essay_score = 0

    def input_essay_score(self,essay_score):
        if essay_score > 60:
            raise ValueError("作文的分数不能超过60")
        else:
            self.essay_score = essay_score
    
    def show_essay_score(self):
        return self.essay_score

    def get_grade(self):
        if self.get_score() >= 135:
            return "优秀"
        elif self.get_score() >= 120:
            return "良好"
        elif self.get_score() >= 90:
            return "及格"
        else:
            return "不及格"
        
if __name__ == "__main__":
    test = ChineseExam("语文",150,"张三")
    test.input_score(95)
    test.input_essay_score(30)
    print(test.show_essay_score())
    print(test.get_grade())
    test.print_report_card()