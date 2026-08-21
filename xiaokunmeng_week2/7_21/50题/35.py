def swap(num_list):
    min = 0
    max = 0
    for i in range(len(num_list)):
        if num_list[i] < num_list[min]:
            min = i
        if num_list[i] > num_list[max]:
            max = i
    if max == 0 and min == len(num_list) - 1:
        return num_list
    elif max == len(num_list) - 1 and min == 0:
        temp = num_list[0]
        num_list[0] = num_list[-1]
        num_list[-1] = temp
    else:
        temp = num_list[0]
        num_list[0] = num_list[max]
        num_list[max] = temp
        temp = num_list[-1]
        num_list[-1] = num_list[min]
        num_list[min] = temp   
    return num_list

print(swap([1,2,3,4,5,6,7,8,9,10]))
print(swap([10,9,8,7,6,5,4,3,2,1]))