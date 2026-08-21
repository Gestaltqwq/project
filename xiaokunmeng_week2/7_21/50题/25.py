def checkout(a):
    num_list = []
    num_list.append(a % 10)
    num_list.append(a % 100 // 10)
    num_list.append(a % 1000 // 100)
    num_list.append(a % 10000 // 1000)
    num_list.append(a // 10000)
    for i in range(round(len(num_list)/2)):
        if num_list[i] == num_list[len(num_list) - i - 1]:
            continue
        else:
            return False
    return True

print(checkout(12321))