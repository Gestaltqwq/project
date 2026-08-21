def sort_method(num_list):
    for i in range(len(num_list)):
        min = i
        for j in range(i + 1,len(num_list)):
            if num_list[j] < num_list[min]:
                min = j
        temp = num_list[i]
        num_list[i] = num_list[min]
        num_list[min] = temp
    return num_list

num_list = [15,7,29]
print(sort_method(num_list))