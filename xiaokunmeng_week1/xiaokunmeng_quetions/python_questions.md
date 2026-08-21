# Python 面试题整理

## Q1：类装饰器的工作原理

### 问题
被装饰的函数名实际上指向了装饰器的实例。请结合 Python 的语法糖，详细描述 `@decorator` 在"定义阶段"和"调用阶段"分别发生了什么？如果装饰器类中同时有 `__init__` 和 `__call__`，它们分别在什么时候触发？如果两个被装饰的函数使用了相同的参数 (3, 2)，它们的缓存会冲突吗？

### 解答

**定义阶段：** Python 执行 `@decorator` 语法糖，等价于 `func = decorator(func)`。此时会触发装饰器类的 `__init__` 方法，创建一个装饰器实例，并将原始函数作为参数传入并保存。

**调用阶段：** 当你调用 `func()` 时，由于 `func` 已指向装饰器实例，触发的是实例的 `__call__` 方法，而不会直接调用原始函数。

**缓存冲突：** 不会冲突。因为每个被装饰的函数对应一个独立的装饰器实例，各自拥有独立的 `_cache` 字典。即使键都是 `(3, 2)`，它们也分别存储在不同的字典中。

```python
# 示例示意
class Decorator:
    def __init__(self, func):
        self.func = func
        self._cache = {}

    def __call__(self, *args):
        if args not in self._cache:
            self._cache[args] = self.func(*args)
        return self._cache[args]

@Decorator
def add(a, b):
    return a + b

@Decorator
def big_calc(a, b):
    return a * b + 100

# add 和 big_calc 各自拥有独立的 _cache 字典
```

---

## Q2：父类私有属性与继承

### 问题
父类的私有属性（如 `__money`）在继承时会传给子类吗？为什么子类无法直接访问？如果父类有 `get_money` 方法，子类能通过它拿到私有值吗？双下划线与单下划线的本质区别是什么？

### 解答

**数据会继承：** 父类的私有属性确实会存在于子类实例的内存中（可通过 `print(c.__dict__)` 看到 `_Parent__money`）。

**无法直接访问的原因：** Python 的 **名称改写（Name Mangling）** 机制会把父类中的 `__money` 编译为 `_Parent__money`。子类访问 `self.__money` 时会被改写为 `_Child__money`，两者名字不一致，因此报错 `AttributeError`。

**能否通过公共方法拿到：** 可以。父类的公共方法（如 `get_money`）在父类作用域内，知道正确的改写名称，因此子类继承后调用该方法可以正常返回私有属性值。

**本质区别：**

| 写法 | 机制 | 含义 |
|------|------|------|
| `__name`（双下划线） | 触发名称改写 → `_ClassName__name` | 强私有，防误触 |
| `_name`（单下划线） | 无改写机制，仅约定 | 保护标志，提示外部不要随意访问，但解释器不做任何阻拦 |

---

## Q3：threading 与 asyncio 的区别

### 问题
`threading`（多线程）和 `asyncio`（异步协程）在处理 I/O 密集型任务时的核心区别是什么？为什么在 `async` 函数中不能用 `time.sleep`，而必须用 `await asyncio.sleep`？如果要处理"纯 CPU 计算"，你会选哪个？

### 解答

**核心区别：**

| 特性 | threading | asyncio |
|------|-----------|---------|
| 调度方式 | 抢占式多任务，由操作系统调度切换线程 | 协作式单线程并发，必须由代码主动 `await` 让出控制权 |
| 适用场景 | I/O 等待（如文件读写） | 高并发网络请求 |
| 并发模型 | 多线程并行 | 单线程事件循环 |

**不能使用 `time.sleep` 的原因：** `time.sleep` 是阻塞整个线程的同步函数，在 `async` 函数中调用会卡住整个事件循环。必须使用 `await asyncio.sleep`，它非阻塞地将控制权交还给事件循环。

**CPU 密集型场景选型：** 都不选，选 `multiprocessing`（多进程）。因为 Python 的 **GIL（全局解释器锁）** 导致 `threading` 和 `asyncio` 都无法利用多核 CPU 并行计算，而多进程可以绕过 GIL 实现真正的并行。

---

## Q4：yield 与 return 的区别

### 问题
`yield` 和 `return` 在函数中的本质区别是什么？包含 `yield` 的函数调用后得到什么？如何获取生成器 yield 出的值？生成器只能遍历一次是否是缺点？

### 解答

**本质区别：**

| 特性 | return | yield |
|------|--------|-------|
| 行为 | 终止函数并销毁局部变量 | 暂停函数并保留局部状态 |
| 返回值次数 | 一次 | 可多次返回值 |
| 函数状态 | 销毁 | 保留 |

**调用结果：** 包含 `yield` 的函数调用后返回一个 **生成器对象（generator）**。

**获取值的方法：** 使用 `next(gen)` 或 `for value in gen:` 迭代。

**关于"只能遍历一次"：** 不能简单说是缺点，而是**设计特性**。生成器设计用于流式处理大文件或无限序列，数据"用完即走"以节省内存。如果需要重复遍历数据，应使用列表或重新创建生成器。

---

## Q5：int() 转换异常处理

### 问题
当 `int("abc")` 转换失败时，Python 是返回 `False` 还是直接报错？真实项目中如何优雅处理并返回默认值？捕获异常时，`except Exception` 和 `except ValueError` 哪个更推荐？

### 解答

**错误表现：** 直接抛出 `ValueError` 异常，**绝不返回 `False`**。

**优雅处理：** 使用 `try-except` 捕获特定异常并返回默认值。

```python
def safe_int(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default
```

**推荐写法：** 优先使用 `except ValueError as e:`。因为它只捕获类型转换错误，而 `except Exception` 会捕获所有异常（包括系统退出信号 `KeyboardInterrupt`），这种"大而全"的写法极易掩盖意外的程序漏洞。

---

## Q6：*args 与 **kwargs 详解

### 问题
请解释 `*args` 和 `**kwargs` 的作用。在定义 `def func(a, b=1, *args, c, **kwargs):` 中，`c` 属于哪类参数？调用时如何将列表 `[1,2,3]` 解包传给 `*args`？

### 解答

**作用：**
- `*args`：接收多余的位置参数并打包为**元组（tuple）**
- `**kwargs`：接收多余的关键字参数并打包为**字典（dict）**

**`c` 的类型：** 属于**命名关键字参数**（必须通过 `func(..., c=value)` 的形式传入，因为它位于 `*args` 之后）。

**解包方法：** 在调用时使用星号解包，即 `func(*[1,2,3])`。

```python
def func(a, b=1, *args, c, **kwargs):
    print(a, b, args, c, kwargs)

# 正确调用
func(10, 20, 1, 2, 3, c=100, name="Alice")
# 输出: 10 20 (1, 2, 3) 100 {'name': 'Alice'}

# 解包列表传给 *args
func(10, 20, *[1, 2, 3], c=100)
```

---

## Q7：match...case 模式匹配

### 问题
`match...case` 中的 `case _:` 有什么作用？它和 C/Java 的 `default` 有何异同？Python 的 `case` 分支会像 C 语言那样"贯穿"（fall through）吗？`match` 能匹配元组结构吗？

### 解答

**`case _:` 的作用：** 通配符，匹配所有未在前置分支中匹配到的值（类似其他语言的 `default`）。

**与 C/Java 的 `default` 异同：**
- 功能上等价于 `default`（兜底匹配）
- 但 Python 的 `match` 功能更强大，支持**解构**和**模式匹配**

**是否会"贯穿"：** 不会。Python 的 `case` 在执行完匹配分支后自动退出，无需像 C 语言那样写 `break`，也不支持贯穿到下一个 `case`。

**能否匹配元组：** 可以。`match` 支持结构模式匹配。

```python
def process(point):
    match point:
        case (0, 0):
            print("原点")
        case (x, 0):
            print(f"X 轴上的点: x={x}")
        case (0, y):
            print(f"Y 轴上的点: y={y}")
        case (x, y):
            print(f"普通点: ({x}, {y})")
        case _:
            print("未知格式")
```

---

## Q8：@abstractmethod 最佳实践

### 问题
使用 `@abstractmethod` 比手动 `raise NotImplementedError` 好在哪？子类忘记实现抽象方法时，两者报错时机有何不同？抽象类中是否允许包含已实现的普通方法？

### 解答

**优势：** `@abstractmethod` 提供了**语法级别的强制约束**，将检查时机提前到了实例化阶段。

**报错时机对比：**

| 方式 | 报错时机 | 发现问题早晚 |
|------|----------|-------------|
| `@abstractmethod` | 实例化子类时立即抛出 `TypeError` | 尽早（实例化即报错） |
| `raise NotImplementedError` | 调用该未实现的方法时才会报错 | 很晚（可能隐藏很久） |

**是否允许普通方法：** 允许。抽象类可以包含完整的普通方法供子类复用（如日志记录、序列号生成等通用逻辑）。

```python
from abc import ABC, abstractmethod

class BaseHandler(ABC):
    @abstractmethod
    def handle(self, data):
        """子类必须实现此方法"""
        pass

    def log(self, message):  # 普通方法，子类可直接复用
        print(f"[LOG] {message}")
```

---

## Q9：time.time() 与 datetime.now() 的使用

### 问题
`time.time()` 和 `datetime.now()` 返回的数据类型分别是什么？计算代码耗时优先选哪个？为什么要用 `int(end - start)` 而不是 `datetime` 相减？`round(2.5)` 为什么输出 2 而不是 3？

### 解答

**数据类型：**

| 函数 | 返回类型 | 说明 |
|------|---------|------|
| `time.time()` | `float` | 时间戳（秒数） |
| `datetime.now()` | `datetime` 对象 | 日期时间对象 |

**首选计算耗时：** 优先使用 `time.time()`。因为它是纯数字，相减直接得到秒数（浮点），无需额外转换，计算效率更高且更灵活。

**不直接用 `datetime` 相减的原因：** `datetime` 相减得到的是 `timedelta` 对象，取秒数需调用 `timedelta.total_seconds()`，稍显繁琐。

```python
import time

start = time.time()
# ... 执行代码 ...
end = time.time()
print(f"耗时: {end - start:.3f} 秒")
```

**`round(2.5)` 输出 2 的原因：** Python 采用 **银行家舍入法（Banker's Rounding）**。当小数位恰好为 `.5` 时，会向**最近的偶数**取整，以消除大量计算中的统计偏误（这是 IEEE 754 标准规定的）。

| 表达式 | 结果 | 说明 |
|--------|------|------|
| `round(2.5)` | `2` | .5 向偶数 2 取整 |
| `round(3.5)` | `4` | .5 向偶数 4 取整 |
| `round(2.4)` | `2` | <.5 向下取整 |
| `round(2.6)` | `3` | >.5 向上取整 |

---

## Q10：逻辑运算符优先级与全局变量

### 问题
请计算 `0 or 1 and 2` 的结果，并解释 `and`/`or` 的优先级及返回值类型（布尔值还是操作数？）。在函数内部修改外部全局变量需要什么关键字？如果不用会发生什么？

### 解答

**计算结果：** `2`

**推导过程：**
```python
0 or 1 and 2
# and 优先级高于 or → 0 or (1 and 2)
# 1 and 2：左为真，返回最后一个操作数 2
# 0 or 2：左为假，返回最后一个操作数 2
# 结果：2
```

**优先级与返回规则：**

| 优先级 | 运算符 | 说明 |
|--------|--------|------|
| 高 | `and` | 先求值 |
| 低 | `or` | 后求值 |

**返回值类型：** 逻辑运算返回的是**最后一个被求值的操作数的值**（而非强制布尔值）。Python 中 `and`/`or` 返回的是操作数本身，不是 `True`/`False`。

**修改全局变量的关键字：** 必须在函数内部使用 `global 变量名` 显式声明。

**如果不声明：** Python 会将赋值操作视为创建一个新的局部变量，外部的全局变量不会被修改（且如果在赋值前尝试读取，可能引发 `UnboundLocalError`）。

```python
count = 0

def increment():
    global count  # 必须声明
    count += 1

def wrong():
    count = 1  # 错误：创建了新局部变量，未修改全局变量
    # 如果这里加 print(count)，会报 UnboundLocalError
```

---

## 附：关键概念速查表

| 概念 | 一句话总结 |
|------|-----------|
| 类装饰器 | `__init__` 在定义时创建实例，`__call__` 在调用时执行 |
| 名称改写 | `__attr` → `_ClassName__attr`，防止子类意外覆盖 |
| GIL | 全局解释器锁，导致多线程无法并行执行 CPU 计算 |
| 生成器 | 用 `yield` 暂停状态，用 `next()` 恢复，适合流式处理 |
| 银行家舍入 | `.5` 向偶数取整，消除统计偏误 |
| `and`/`or` 短路 | 返回最后求值的操作数，而非布尔值 |
| global 声明 | 在函数内修改全局变量的必要关键字 |
