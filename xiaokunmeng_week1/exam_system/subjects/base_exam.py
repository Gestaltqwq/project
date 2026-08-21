from abc import ABC,abstractmethod

class BaseExam(ABC):
    passing_rate = 0.6 #及格率
    def __init__(self,subject_name:str,max_score:float,student_name:str):
        self.subject_name = subject_name
        self.max_score = max_score
        self.student_name = student_name
        self.__score = 0

    def get_score(self) -> float:
        return self.__score
    def input_score(self,score:float):
        if score > self.max_score:
            raise ValueError(f"{self.subject_name}的分数不能超过{self.max_score}")
        elif score < 0:
            raise ValueError(f"{self.subject_name}的分数不能小于0")
        self.__score = score

    @classmethod
    def set_passing_rate(cls,rate:float):
        cls.passing_rate = rate

    @staticmethod
    def check_student_name(name:str) -> bool:
        if name == "":
            return False
        for i in name:
            if i.isdigit():
                return False
            elif i.isspace():
                return False
            elif i.isalpha():
                continue
            else:
                return False
        return True
    def get_grade(self) -> str:
        raise NotImplementedError("该子类未实现该方法")
    
    def calc_weighted_score(self,weight) -> float:
        return round(self.__score * weight, 2)

    def print_report_card(self):
        score = self.get_score()
        print(f"学生:{self.student_name}")
        print(f"科目:{self.subject_name}")
        print(f"成绩:{score}")
        print(f"等级:{self.get_grade()}")
        print(f"加权:{self.calc_weighted_score(0.7)}")

