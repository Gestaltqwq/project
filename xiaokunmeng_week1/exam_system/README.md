# 考试成绩管理系统

一个基于 Python 面向对象设计的考试成绩管理系统，支持多学科成绩管理、分数校验、线程安全录入、偏科检测等功能。

## 项目结构

```
exam_system/
├── main.py                  # 程序入口，演示各模块功能
├── grade_utils.py           # 成绩工具函数
├── README.md                # 本文件
└── subjects/                # 学科模块包
    ├── __init__.py           # 包入口，导出所有学科类
    ├── base_exam.py          # 抽象基类 BaseExam
    ├── chinese.py            # 语文考试子类
    ├── math.py               # 数学考试子类（支持附加分）
    └── english.py            # 英语考试子类（自定义成绩单）
```

## 模块说明

### subjects 包 — 学科类体系

| 类 | 说明 | 特有功能 |
|---|---|---|
| `BaseExam` | 抽象基类，定义考试通用属性和接口 | 及格率设置、加权分计算、通用成绩单 |
| `ChineseExam` | 语文考试，继承 BaseExam | 作文分录入与展示 |
| `MathExam` | 数学考试，继承 BaseExam | 附加分设置与加权 |
| `EnglishExam` | 英语考试，继承 BaseExam | 定制成绩单（含听力/阅读/写作） |

**基类核心方法：**

- `input_score(score)` — 输入分数，自动校验范围（0 ~ max_score）
- `get_score()` — 获取原始分
- `get_grade()` — 获取等级（各学科自定义标准）
- `calc_weighted_score(weight)` — 计算加权分
- `set_passing_rate(rate)` — 类方法，设置全局及格率
- `check_student_name(name)` — 静态方法，校验姓名合法性
- `print_report_card()` — 打印成绩单

### grade_utils.py — 工具函数

| 函数 | 说明 |
|---|---|
| `check_valid_score(score, max_score)` | 检查分数是否在有效范围内 |
| `calc_percentage(score, max_score)` | 计算得分率百分比 |
| `save_record(record_info)` | 将记录写入 `exam_records.txt` |
| `read_all_records()` | 读取 `exam_records.txt` 全部记录 |
| `get_excellent_students(score_list, threshold)` | 筛选优秀学生 |
| `report_card_generator(student_list)` | 生成成绩报告卡 |
| `input_score_thread_safe(name, subject, score)` | 线程安全地录入成绩 |
| `multi_thread_input_test()` | 多线程录入测试 |
| `check_balance(student_score)` | 检测各科均衡性 |

## 成绩等级标准

| 科目 | 优秀 | 良好 | 及格 | 不及格 |
|---|---|---|---|---|
| 语文 | ≥ 135 | ≥ 120 | ≥ 90 | < 90 |
| 数学 | ≥ 140 | ≥ 120 | ≥ 90 | < 90 |
| 英语 | ≥ 90  | ≥ 75  | ≥ 60 | < 60 |

## 使用方式

```bash
cd exam_system
python main.py
```

运行 `main.py` 将依次执行以下测试：

1. 基础得分率计算
2. 成绩保存与读取
3. 多线程录入
4. 语文、数学、英语三科考试流程
5. 优秀学生筛选
6. 成绩单生成
7. 批量统计（多态）
8. 偏科检测
