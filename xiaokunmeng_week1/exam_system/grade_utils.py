import threading
student_records = {}
record_lock = threading.Lock()
def check_valid_score(score, max_score):
    """检查分数是否在有效范围内（0 ~ max_score）"""
    if score > max_score or score < 0:
        return False
    else:
        return True
def calc_percentage(score, max_score):
    """计算分数占总分的百分比"""
    return score / max_score * 100
def save_record(record_info):
    """将一条考试记录追加写入 exam_records.txt 文件"""
    with open("exam_records.txt", "a", encoding="utf-8") as f:
        f.write(record_info + "\n")
def read_all_records():
    """读取 exam_records.txt 中所有记录，返回非空行的列表"""
    records = []
    with open("exam_records.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line != "":
                records.append(line)
        return records

def get_excellent_students(score_list,threshold):
    """筛选出成绩达到或超过指定阈值的优秀学生名单"""
    result = [
        student for student, score in score_list.items() if score >= threshold
    ]
    return result

def report_card_generator(student_list):
    """为每个学生生成成绩报告卡（学生姓名/学科/成绩/等级）"""
    for exam in student_list:
        return (
            f"学生:{exam.student_name}",
            f"学科:{exam.subject_name}",
            f"成绩:{exam.get_score()}",
            f"等级:{exam.get_grade()}",
        )
def input_score_thread_safe(student_name,subject,score):
    """线程安全地录入学生成绩，使用锁避免并发写入冲突"""
    with record_lock:
        if student_name not in student_records:
            student_records[student_name] = {}
        student_records[student_name][subject] = score

def multi_thread_input_test():
    """多线程录入测试——启动两个线程同时录入张三的语文和数学成绩"""
    t1 = threading.Thread(target=input_score_thread_safe, args=("张三", "语文", 80))
    t2 = threading.Thread(target=input_score_thread_safe, args=("张三", "数学", 130))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("录入完成")
    print(student_records)

def check_balance(student_score):
    """检查学生各科成绩是否均衡，按偏差程度输出"各科均衡"/"轻微偏科"/"严重偏科"及偏科科目"""
    count = 0
    score_sum = 0
    delta_sum = 0
    for subject, score in student_score.items():
        count += 1
        score_sum += score
    average = round(score_sum / count, 2)
    for subject, score in student_score.items():
        delta_sum += abs(score - average)**2
    deviation = round((delta_sum / count ** 0.5), 2)
    if deviation < 10:
        print("各科均衡")
    elif deviation < 20:
        print("轻微偏科")
    elif deviation >= 20:
        worst_subject = max(student_score, key=lambda x: abs(student_score[x] - average))
        print(f"严重偏科，偏科科目为：{worst_subject}")
        
